import duckdb
import sys
import os
import socket

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def is_minio_online(host="localhost", port=9000):
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False

print("⏳ Đang khởi tạo kết nối DuckDB...")
con = duckdb.connect()

minio_active = is_minio_online()
if minio_active:
    print("🌐 Phát hiện MinIO S3 đang hoạt động (localhost:9000). Cấu hình HTTPFS...")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("""
        SET s3_endpoint='localhost:9000';
        SET s3_access_key_id='admin';
        SET s3_secret_access_key='password123';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
    """)
else:
    print("ℹ️ MinIO S3 chưa khởi chạy, hệ thống sẽ lưu và truy vấn Parquet trực tiếp tại data/silver.")

# 1. Đọc dữ liệu Bronze JSON vào view tạm
print("⏳ Đang đọc dữ liệu Bronze từ data/mock_bronze_tiki.json...")
con.execute("""
    CREATE OR REPLACE VIEW raw_bronze AS 
    SELECT * FROM read_json_auto('data/mock_bronze_tiki.json');
""")

# 2. Xuất dữ liệu Silver (dim_product, dim_date, fact_daily_prices)
print("⏳ Đang xuất dữ liệu Silver...")

def export_parquet(query, s3_path, local_path, is_partitioned=False):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if is_partitioned:
        con.execute(f"COPY ({query}) TO '{local_path}' (FORMAT PARQUET, COMPRESSION SNAPPY, PARTITION_BY (year, month), OVERWRITE_OR_IGNORE 1);")
    else:
        con.execute(f"COPY ({query}) TO '{local_path}' (FORMAT PARQUET, COMPRESSION SNAPPY);")
        
    if minio_active:
        try:
            if is_partitioned:
                con.execute(f"COPY ({query}) TO '{s3_path}' (FORMAT PARQUET, COMPRESSION SNAPPY, PARTITION_BY (year, month), OVERWRITE_OR_IGNORE 1);")
            else:
                con.execute(f"COPY ({query}) TO '{s3_path}' (FORMAT PARQUET, COMPRESSION SNAPPY);")
        except Exception as e:
            print(f"⚠️ Lỗi xuất S3: {e}")

dim_product_query = """
    SELECT DISTINCT
        product_id,
        sku,
        name AS product_name,
        brand,
        category_name
    FROM raw_bronze
"""
export_parquet(dim_product_query, 's3://lakehouse-warehouse/silver/dim_product/dim_product.parquet', 'data/silver/dim_product/dim_product.parquet')

dim_date_query = """
    WITH distinct_dates AS (
        SELECT DISTINCT CAST(crawled_date AS DATE) AS full_date 
        FROM raw_bronze
    )
    SELECT 
        CAST(strftime(full_date, '%Y%m%d') AS INTEGER) AS date_key,
        full_date,
        dayofweek(full_date) AS day_of_week,
        month(full_date) AS month,
        quarter(full_date) AS quarter,
        year(full_date) AS year,
        CASE WHEN dayofweek(full_date) IN (1, 7) THEN true ELSE false END AS is_weekend
    FROM distinct_dates
"""
export_parquet(dim_date_query, 's3://lakehouse-warehouse/silver/dim_date/dim_date.parquet', 'data/silver/dim_date/dim_date.parquet')

fact_prices_query = """
    SELECT 
        product_id,
        CAST(strftime(CAST(crawled_date AS DATE), '%Y%m%d') AS INTEGER) AS date_key,
        price,
        market_price,
        discount_rate,
        rating_score,
        review_count,
        year(CAST(crawled_date AS DATE)) AS year,
        month(CAST(crawled_date AS DATE)) AS month
    FROM raw_bronze
"""
export_parquet(fact_prices_query, 's3://lakehouse-warehouse/silver/fact_daily_prices', 'data/silver/fact_daily_prices', is_partitioned=True)

print("✅ Đã tạo thành công mô hình Star-Schema dạng Parquet bằng DuckDB!")