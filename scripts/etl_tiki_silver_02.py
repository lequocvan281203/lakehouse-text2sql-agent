import os
import duckdb

# 1. Khởi tạo kết nối DuckDB và cấu hình S3 MinIO
con = duckdb.connect()

con.execute("""
    INSTALL httpfs;
    LOAD httpfs;
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='admin';
    SET s3_secret_access_key='password123';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
""")

print("🚀 Khởi chạy ETL: Bronze CSV -> Silver Star-Schema Parquet (Tiki Books)...")

# 2. Xử lý Bảng Chiều Sách: dim_book
# Loại bỏ trùng lặp product_id, chuẩn hóa dữ liệu text
print("\n⏳ Đang trích xuất và tối ưu hóa bảng: dim_book...")
con.execute("""
    CREATE OR REPLACE TABLE dim_book AS
    SELECT 
        CAST(product_id AS BIGINT) AS book_id,
        TRIM(title) AS title,
        TRIM(COALESCE(authors, 'Unknown')) AS authors,
        TRIM(COALESCE(category, 'Others')) AS category,
        TRIM(COALESCE(manufacturer, 'Unknown')) AS manufacturer,
        TRY_CAST(pages AS INTEGER) AS pages,
        TRIM(cover_link) AS cover_link
    FROM read_csv(
        's3://lakehouse-warehouse/bronze/tiki_books/book_data.csv',
        header=True,
        auto_detect=True,
        encoding='utf-8',
        ignore_errors=True
    )
    WHERE product_id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY current_price DESC) = 1;
""")

book_count = con.execute("SELECT count(*) FROM dim_book").fetchone()[0]
print(f"✅ Bảng dim_book hoàn thành: {book_count} cuốn sách (duy nhất).")

# 3. Xử lý Bảng Sự Kiện Hiệu Suất Sách: fact_book_performance
# Tính toán các chỉ số: Tiền giảm giá, Tỷ lệ giảm giá, Doanh thu ước tính
print("\n⏳ Đang xử lý bảng sự kiện: fact_book_performance...")
con.execute("""
    CREATE OR REPLACE TABLE fact_book_performance AS
    SELECT 
        CAST(b.product_id AS BIGINT) AS book_id,
        TRIM(COALESCE(b.category, 'Others')) AS category,
        CAST(b.current_price AS DOUBLE) AS current_price,
        CAST(COALESCE(b.original_price, b.current_price) AS DOUBLE) AS original_price,
        ROUND(CAST(COALESCE(b.original_price, b.current_price) AS DOUBLE) - CAST(b.current_price AS DOUBLE), 0) AS discount_amount,
        ROUND(
            CASE 
                WHEN COALESCE(b.original_price, 0) > b.current_price 
                THEN ((b.original_price - b.current_price) / b.original_price) * 100 
                ELSE 0.0 
            END, 1
        ) AS discount_percentage,
        CAST(COALESCE(b.quantity, 0) AS BIGINT) AS quantity_sold,
        ROUND(CAST(b.current_price AS DOUBLE) * CAST(COALESCE(b.quantity, 0) AS BIGINT), 0) AS estimated_revenue,
        ROUND(CAST(COALESCE(b.avg_rating, 0.0) AS DOUBLE), 2) AS avg_rating,
        CAST(COALESCE(b.n_review, 0) AS BIGINT) AS review_count
    FROM read_csv(
        's3://lakehouse-warehouse/bronze/tiki_books/book_data.csv',
        header=True,
        auto_detect=True,
        encoding='utf-8',
        ignore_errors=True
    ) b
    WHERE b.product_id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY b.product_id ORDER BY b.current_price DESC) = 1;
""")

fact_count = con.execute("SELECT count(*) FROM fact_book_performance").fetchone()[0]
print(f"✅ Bảng fact_book_performance hoàn thành: {fact_count} bản ghi sự kiện.")

# 4. Xử lý Bảng Sự Kiện Đánh Giá: fact_book_reviews
print("\n⏳ Đang trích xuất bảng sự kiện đánh giá: fact_book_reviews...")
con.execute("""
    CREATE OR REPLACE TABLE fact_book_reviews AS
    SELECT 
        CAST(comment_id AS BIGINT) AS comment_id,
        CAST(product_id AS BIGINT) AS book_id,
        CAST(customer_id AS BIGINT) AS customer_id,
        CAST(customer_rating AS DOUBLE) AS rating,
        CAST(COALESCE(thank_count, 0) AS BIGINT) AS thank_count,
        TRIM(COALESCE(title, '')) AS review_title,
        TRIM(COALESCE(content, '')) AS review_content
    FROM read_csv(
        's3://lakehouse-warehouse/bronze/tiki_books/comments.csv',
        header=True,
        auto_detect=True,
        encoding='utf-8',
        ignore_errors=True
    )
    WHERE comment_id IS NOT NULL AND product_id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY comment_id ORDER BY customer_rating DESC) = 1;
""")

review_count = con.execute("SELECT count(*) FROM fact_book_reviews").fetchone()[0]
print(f"✅ Bảng fact_book_reviews hoàn thành: {review_count} lượt đánh giá.")

# 5. Xuất các bảng sang định dạng Parquet nén Snappy trên MinIO Silver Layer
print("\n💾 Đang ghi dữ liệu Parquet lên MinIO s3://lakehouse-warehouse/silver/tiki_books/ ...")

# Xuất dim_book
con.execute("""
    COPY dim_book TO 's3://lakehouse-warehouse/silver/tiki_books/dim_book/dim_book.parquet' 
    (FORMAT PARQUET, COMPRESSION SNAPPY);
""")
print("  -> Ghi thành công: dim_book.parquet")

# Xuất fact_book_performance có Partition theo category
con.execute("""
    COPY fact_book_performance TO 's3://lakehouse-warehouse/silver/tiki_books/fact_book_performance/' 
    (FORMAT PARQUET, COMPRESSION SNAPPY, PARTITION_BY (category));
""")
print("  -> Ghi thành công: fact_book_performance (Partitioned theo category)")

# Xuất fact_book_reviews
con.execute("""
    COPY fact_book_reviews TO 's3://lakehouse-warehouse/silver/tiki_books/fact_book_reviews/reviews.parquet' 
    (FORMAT PARQUET, COMPRESSION SNAPPY);
""")
print("  -> Ghi thành công: reviews.parquet")

print("\n🎉 Hoàn thành toàn diện Pha 2! Toàn bộ Star-Schema Parquet đã sẵn sàng trên MinIO Silver.")