import duckdb

def get_duckdb_lakehouse():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    # Cấu hình đọc S3/MinIO
    con.execute("""
        SET s3_endpoint='localhost:9000';
        SET s3_access_key_id='admin';
        SET s3_secret_access_key='password123';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
    """)
    
    # 1. Base Views: Ánh xạ trực tiếp từ các file Parquet trên MinIO
    con.execute("""
        CREATE OR REPLACE VIEW v_dim_product AS 
        SELECT * FROM read_parquet('s3://lakehouse-warehouse/silver/dim_product/*.parquet');
        
        CREATE OR REPLACE VIEW v_dim_date AS 
        SELECT * FROM read_parquet('s3://lakehouse-warehouse/silver/dim_date/*.parquet');
        
        CREATE OR REPLACE VIEW v_fact_prices AS 
        SELECT * FROM read_parquet('s3://lakehouse-warehouse/silver/fact_daily_prices/*/*/*.parquet');
    """)
    
    # 2. Semantic View: Lớp ngữ nghĩa kinh doanh tổng hợp
    con.execute("""
        CREATE OR REPLACE VIEW semantic_daily_product_insights AS
        SELECT 
            f.product_id,
            p.product_name,
            p.brand,
            p.category_name,
            d.full_date,
            d.day_of_week,
            d.is_weekend,
            f.price AS current_price,
            f.market_price,
            (f.market_price - f.price) AS discount_amount,
            ROUND(f.discount_rate * 100, 1) AS discount_percentage,
            f.rating_score,
            f.review_count
        FROM v_fact_prices f
        JOIN v_dim_product p ON f.product_id = p.product_id
        JOIN v_dim_date d ON f.date_key = d.date_key;
    """)
    
    return con

if __name__ == "__main__":
    con = get_duckdb_lakehouse()
    print("✅ Đã kết nối MinIO và nạp thành công Semantic Layer!")
    print("\n--- TEST QUERY 1: TOP 5 SẢN PHẨM GIẢM GIÁ SÂU NHẤT ---")
    query_1 = """
        SELECT 
            product_name, 
            brand, 
            current_price, 
            discount_percentage
        FROM semantic_daily_product_insights
        WHERE discount_percentage > 0
        ORDER BY discount_percentage DESC
        LIMIT 5;
    """
    print(con.execute(query_1).df().to_string(index=False))

    print("\n--- TEST QUERY 2: GIÁ TRUNG BÌNH & MỨC GIẢM THEO THƯƠNG HIỆU ---")
    query_2 = """
        SELECT 
            brand,
            COUNT(DISTINCT product_id) AS total_products,
            ROUND(AVG(current_price), 0) AS avg_selling_price,
            ROUND(AVG(discount_percentage), 1) AS avg_discount_pct
        FROM semantic_daily_product_insights
        GROUP BY brand
        ORDER BY avg_selling_price DESC;
    """
    print(con.execute(query_2).df().to_string(index=False))