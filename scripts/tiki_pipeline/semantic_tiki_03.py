import os
import sys
import duckdb

def get_duckdb_tiki_lakehouse():
    """Khởi tạo kết nối DuckDB kết nối trực tiếp đến MinIO Silver Layer của Tiki Books."""
    con = duckdb.connect()
    
    # Cấu hình httpfs đọc S3 MinIO
    con.execute("""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_endpoint='localhost:9000';
        SET s3_access_key_id='admin';
        SET s3_secret_access_key='password123';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
    """)
    
    # Tạo View ngữ nghĩa tổng hợp toàn bộ thông tin sách và chỉ số bán hàng
    con.execute("""
        CREATE OR REPLACE VIEW semantic_tiki_book_insights AS
        SELECT 
            b.book_id,
            b.title AS book_title,
            b.authors,
            b.category,
            b.manufacturer,
            b.pages,
            b.cover_link,
            f.current_price,
            f.original_price,
            f.discount_amount,
            f.discount_percentage,
            f.quantity_sold,
            f.estimated_revenue,
            f.avg_rating,
            f.review_count
        FROM read_parquet('s3://lakehouse-warehouse/silver/tiki_books/dim_book/dim_book.parquet') b
        JOIN read_parquet('s3://lakehouse-warehouse/silver/tiki_books/fact_book_performance/*/*.parquet') f
            ON b.book_id = f.book_id;
    """)
    return con

if __name__ == "__main__":
    print("⏳ Đang kết nối DuckDB tới MinIO và khởi tạo View 'semantic_tiki_book_insights'...")
    con = get_duckdb_tiki_lakehouse()
    
    print("\n🔍 Kiểm tra dữ liệu Semantic Layer (Top 3 cuốn sách có doanh thu ước tính cao nhất):")
    df = con.execute("""
        SELECT book_title, authors, category, current_price, quantity_sold, estimated_revenue, avg_rating
        FROM semantic_tiki_book_insights
        ORDER BY estimated_revenue DESC
        LIMIT 3;
    """).df()
    print(df.to_string(index=False))