import duckdb

# Kết nối DuckDB in-memory và cấu hình S3 MinIO
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

print("--- 1. CẤU TRÚC FILE book_data.csv ---")
df_book = con.execute("""
    SELECT * 
    FROM read_csv_auto('s3://lakehouse-warehouse/bronze/tiki_books/book_data.csv') 
    LIMIT 3;
""").df()
print(df_book.columns.tolist())
print(df_book.head(2))

print("\n--- 2. CẤU TRÚC FILE comments.csv ---")
try:
    df_comments = con.execute("""
        SELECT * 
        FROM read_csv_auto('s3://lakehouse-warehouse/bronze/tiki_books/comments.csv') 
        LIMIT 3;
    """).df()
    print(df_comments.columns.tolist())
    print(df_comments.head(2))
except Exception as e:
    print(f"Lỗi khi đọc comments.csv: {e}")