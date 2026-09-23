METADATA_CHUNKS = [
    {
        "id": "table_semantic_daily_product_insights",
        "type": "table_schema",
        "title": "Bảng dữ liệu phân tích sản phẩm hàng ngày (semantic_daily_product_insights)",
        "content": """
        Bảng view chính phục vụ truy vấn phân tích e-commerce: semantic_daily_product_insights.
        Bao gồm các thông tin sản phẩm, thương hiệu, danh mục, thời gian, giá bán và đánh giá.
        Cấu trúc cột:
        - product_id (VARCHAR): Mã định danh duy nhất của sản phẩm.
        - product_name (VARCHAR): Tên đầy đủ của sản phẩm.
        - brand (VARCHAR): Thương hiệu (Apple, Dell, Asus, Logitech, Samsung, Sony).
        - category_name (VARCHAR): Ngành hàng (Laptop, Smartphone, Tai nghe, Màn hình, Bàn phím cơ).
        - full_date (DATE): Ngày ghi nhận dữ liệu (định dạng YYYY-MM-DD).
        - day_of_week (INTEGER): Thứ trong tuần (1 = Chủ nhật, 2 = Thứ 2, ..., 7 = Thứ 7).
        - is_weekend (BOOLEAN): true nếu là Thứ 7 hoặc Chủ nhật, false nếu là ngày trong tuần.
        - current_price (DOUBLE): Giá bán thực tế hiện tại (VNĐ).
        - market_price (DOUBLE): Giá niêm yết gốc của sản phẩm (VNĐ).
        - discount_amount (DOUBLE): Số tiền được giảm (market_price - current_price).
        - discount_percentage (DOUBLE): Tỷ lệ giảm giá tính theo phần trăm (0 - 100%).
        - rating_score (DOUBLE): Điểm đánh giá trung bình từ người mua (thang điểm 1 - 5).
        - review_count (BIGINT): Tổng số lượng đánh giá/bình luận.
        """
    },
    {
        "id": "metrics_definitions",
        "type": "business_logic",
        "title": "Quy tắc nghiệp vụ và công thức tính toán",
        "content": """
        Quy ước tính toán số liệu kinh doanh:
        - Giá bán trung bình của thương hiệu: ROUND(AVG(current_price), 0).
        - Tỷ lệ giảm giá trung bình: ROUND(AVG(discount_percentage), 1).
        - Sản phẩm giảm giá sâu / Sale khủng: Điều kiện WHERE discount_percentage > 0 ORDER BY discount_percentage DESC.
        - Sản phẩm bán chạy / uy tín cao: Có rating_score >= 4.5 và review_count cao.
        - So sánh ngày thường và cuối tuần: GROUP BY is_weekend hoặc day_of_week.
        """
    },
    {
        "id": "sql_fewshot_examples",
        "type": "examples",
        "title": "Các câu hỏi mẫu và câu truy vấn DuckDB SQL tương ứng",
        "content": """
        Câu hỏi: Top 5 sản phẩm của hãng Apple có điểm đánh giá cao nhất?
        SQL: SELECT product_name, brand, rating_score, review_count FROM semantic_daily_product_insights WHERE LOWER(brand) = 'apple' ORDER BY rating_score DESC, review_count DESC LIMIT 5;

        Câu hỏi: Giá trung bình của từng danh mục sản phẩm là bao nhiêu?
        SQL: SELECT category_name, ROUND(AVG(current_price), 0) AS avg_price FROM semantic_daily_product_insights GROUP BY category_name ORDER BY avg_price DESC;

        Câu hỏi: Thương hiệu nào có mức giảm giá trung bình cao nhất?
        SQL: SELECT brand, ROUND(AVG(discount_percentage), 1) AS avg_discount FROM semantic_daily_product_insights GROUP BY brand ORDER BY avg_discount DESC LIMIT 1;
        """
    }
]