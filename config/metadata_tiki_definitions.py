"""
Định nghĩa metadata, business rules và few-shot SQL examples cho Tiki Books Lakehouse.
"""

TIKI_METADATA_CHUNKS = [
    {
        "id": "tiki_schema_semantic_insights",
        "title": "Schema view ngữ nghĩa semantic_tiki_book_insights",
        "content": """
BẢNG VIEW CHÍNH: `semantic_tiki_book_insights`
Mục đích: Cung cấp đầy đủ thông tin sách, tác giả, giá bán và hiệu suất kinh doanh trên Tiki.

DANH SÁCH CÁC CỘT:
- `book_id` (BIGINT): Mã định danh duy nhất của cuốn sách trên Tiki.
- `book_title` (VARCHAR): Tên tựa sách đầy đủ.
- `authors` (VARCHAR): Tên tác giả (hoặc 'Unknown' nếu không rõ).
- `category` (VARCHAR): Thể loại sách (Ví dụ: 'Tiểu Thuyết', 'Sách kinh tế', 'Sách Kỹ Năng', 'Others'...).
- `manufacturer` (VARCHAR): Tên nhà xuất bản hoặc đơn vị phát hành.
- `pages` (INTEGER): Số trang sách.
- `current_price` (DOUBLE): Giá bán khuyến mãi hiện tại (VNĐ).
- `original_price` (DOUBLE): Giá niêm yết gốc của sách (VNĐ).
- `discount_amount` (DOUBLE): Số tiền được giảm (original_price - current_price) (VNĐ).
- `discount_percentage` (DOUBLE): Tỷ lệ phần trăm giảm giá (%).
- `quantity_sold` (BIGINT): Số lượng sách đã bán được.
- `estimated_revenue` (DOUBLE): Doanh thu ước tính (current_price * quantity_sold) (VNĐ).
- `avg_rating` (DOUBLE): Điểm đánh giá trung bình của người mua (thang điểm từ 1.0 đến 5.0).
- `review_count` (BIGINT): Tổng số lượt đánh giá của khách hàng.
"""
    },
    {
        "id": "tiki_business_rules",
        "title": "Quy tắc nghiệp vụ và chỉ số phân tích sách",
        "content": """
QUY TẮC NGHIỆP VỤ & TÍNH TOÁN:
1. Sách Bán Chạy (Best Seller): Lọc hoặc sắp xếp giảm dần theo `quantity_sold DESC` hoặc `estimated_revenue DESC`.
2. Sách Được Yêu Thích / Đánh Giá Cao: Lọc theo `avg_rating >= 4.5` và nên có `review_count >= 50` để đảm bảo độ tin cậy.
3. Sách Giảm Giá Nhiều / Khuyến Mãi Khủng: Sắp xếp theo `discount_percentage DESC`.
4. Tìm kiếm từ khóa theo tên sách hoặc tác giả: Sử dụng `ILIKE '%từ_khóa%'` để tìm kiếm không phân biệt hoa thường.
5. Chỉ truy vấn từ duy nhất bảng view `semantic_tiki_book_insights`.
"""
    },
    {
        "id": "tiki_fewshot_sql",
        "title": "Các câu hỏi mẫu và câu truy vấn DuckDB SQL tương ứng",
        "content": """
VÍ DỤ TRUY VẤN MẪU:

Câu hỏi: Top 5 cuốn sách tiểu thuyết có doanh thu ước tính cao nhất?
SQL:
SELECT book_title, authors, current_price, quantity_sold, estimated_revenue
FROM semantic_tiki_book_insights
WHERE category ILIKE '%tiểu thuyết%'
ORDER BY estimated_revenue DESC
LIMIT 5;

Câu hỏi: Thể loại sách nào có số lượng bán trung bình cao nhất?
SQL:
SELECT category, ROUND(AVG(quantity_sold), 0) AS avg_quantity_sold, COUNT(*) AS total_books
FROM semantic_tiki_book_insights
GROUP BY category
ORDER BY avg_quantity_sold DESC;

Câu hỏi: Những cuốn sách nào của tác giả Nguyễn Nhật Ánh có điểm đánh giá từ 4.8 trở lên?
SQL:
SELECT book_title, avg_rating, review_count, current_price
FROM semantic_tiki_book_insights
WHERE authors ILIKE '%Nguyễn Nhật Ánh%' AND avg_rating >= 4.8
ORDER BY avg_rating DESC, review_count DESC;

Câu hỏi: Top 3 nhà xuất bản có nhiều đầu sách nhất?
SQL:
SELECT manufacturer, COUNT(book_id) AS total_books
FROM semantic_tiki_book_insights
WHERE manufacturer != 'Unknown'
GROUP BY manufacturer
ORDER BY total_books DESC
LIMIT 3;
"""
    }
]