import duckdb

print("⏳ Đang khởi tạo kết nối DuckDB và cấu hình MinIO S3...")
con = duckdb.connect()

# Cài đặt extension hỗ trợ S3/MinIO và Parquet
con.execute("INSTALL httpfs; LOAD httpfs;")

# Cấu hình kết nối MinIO
con.execute("""
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='admin';
    SET s3_secret_access_key='password123';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
""")

# 1. Đọc dữ liệu Bronze JSON vào view tạm
print("⏳ Đang đọc dữ liệu Bronze từ data/mock_bronze_tiki.json...")
con.execute("""
    CREATE OR REPLACE VIEW raw_bronze AS 
    SELECT * FROM read_json_auto('data/mock_bronze_tiki.json');
""")

# 2. Tạo và ghi dim_product ra MinIO dưới dạng Parquet
print("⏳ Đang xuất silver/dim_product...")
con.execute("""
    COPY (
        SELECT DISTINCT
            product_id,
            sku,
            name AS product_name,
            brand,
            category_name
        FROM raw_bronze
    ) TO 's3://lakehouse-warehouse/silver/dim_product/dim_product.parquet' (FORMAT PARQUET, COMPRESSION SNAPPY);
""")

# 3. Tạo và ghi dim_date ra MinIO dưới dạng Parquet
print("⏳ Đang xuất silver/dim_date...")
con.execute("""
    COPY (
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
    ) TO 's3://lakehouse-warehouse/silver/dim_date/dim_date.parquet' (FORMAT PARQUET, COMPRESSION SNAPPY);
""")

# 4. Tạo và ghi fact_daily_prices ra MinIO dưới dạng Parquet (có Partition theo year và month)
print("⏳ Đang xuất silver/fact_daily_prices...")
con.execute("""
    COPY (
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
    ) TO 's3://lakehouse-warehouse/silver/fact_daily_prices' (
        FORMAT PARQUET, 
        COMPRESSION SNAPPY, 
        PARTITION_BY (year, month), 
        OVERWRITE_OR_IGNORE 1
    );
""")

print("✅ Đã tạo thành công mô hình Star-Schema trên MinIO (S3) dạng Parquet bằng DuckDB!")