import os
import sys
import streamlit as st
import pandas as pd

# Thêm thư mục gốc vào path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from scripts.mock_pipeline.langgraph_agent_05 import agent_app as mock_agent_app, duckdb_con as mock_duckdb_con
from scripts.tiki_pipeline.langgraph_tiki_agent_05 import tiki_agent_app, duckdb_tiki_con

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="Multi-Lakehouse AI Analytics Agent",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Data Lakehouse AI Analytics Agent")
st.caption("Kiến trúc MinIO (S3 Parquet) + DuckDB Semantic Layer + Metadata RAG (ChromaDB) + LangGraph Multi-Agent (Gemini)")

# Sidebar: Lựa chọn Dataset & Xem trước dữ liệu
with st.sidebar:
    st.header("🗄️ Chọn Nguồn Dữ Liệu")
    dataset_mode = st.radio(
        "Data Source:",
        ["Tiki Books (Real Dataset)", "Mock E-Commerce (Synthetic)"],
        index=0
    )

    if dataset_mode == "Tiki Books (Real Dataset)":
        active_agent = tiki_agent_app
        active_con = duckdb_tiki_con
        view_name = "semantic_tiki_book_insights"
        sample_query = "SELECT book_title, authors, category, current_price, quantity_sold, estimated_revenue, avg_rating FROM semantic_tiki_book_insights LIMIT 5;"
        st.divider()
        st.markdown("""
        **Gợi ý câu hỏi Tiki Books:**
        - *Top 5 cuốn sách tiểu thuyết có doanh thu ước tính cao nhất?*
        - *Thể loại sách nào có điểm đánh giá trung bình cao nhất?*
        - *Top 3 cuốn sách giảm giá nhiều nhất của tác giả Nguyễn Nhật Ánh.*
        """)
    else:
        active_agent = mock_agent_app
        active_con = mock_duckdb_con
        view_name = "semantic_daily_product_insights"
        sample_query = "SELECT product_name, brand, category_name, current_price, discount_percentage FROM semantic_daily_product_insights LIMIT 5;"
        st.divider()
        st.markdown("""
        **Gợi ý câu hỏi Mock:**
        - *Thương hiệu nào có tỷ lệ giảm giá trung bình cao nhất?*
        - *Top 5 sản phẩm có lượt đánh giá cao nhất của hãng Apple.*
        """)

    st.divider()
    st.write(f"View đang kết nối: `{view_name}`")
    if st.button("Xem mẫu 5 dòng dữ liệu"):
        try:
            preview_df = active_con.execute(sample_query).df()
            st.dataframe(preview_df)
        except Exception as e:
            st.error(f"Lỗi: {e}")

# Quản lý phiên hội thoại cho từng nguồn
session_key = f"messages_{dataset_mode}"
if session_key not in st.session_state:
    st.session_state[session_key] = []

# Hiển thị lịch sử chat
for msg in st.session_state[session_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg and msg["data"] is not None:
            st.dataframe(msg["data"])

# Nhận input từ người dùng
user_input = st.chat_input(f"Đặt câu hỏi phân tích cho {dataset_mode}...")

if user_input:
    st.session_state[session_key].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm metadata, dịch SQL và thực thi trên Lakehouse..."):
            initial_state = {
                "user_query": user_input,
                "retry_count": 0,
                "error_message": None
            }
            output = active_agent.invoke(initial_state)

            gen_sql = output.get("generated_sql", "")
            explanation = output.get("final_answer", "")

            st.markdown("#### 🛠️ Câu lệnh DuckDB SQL:")
            st.code(gen_sql, language="sql")

            df_result = None
            try:
                df_result = active_con.execute(gen_sql).df()
                if not df_result.empty:
                    st.markdown("#### 📋 Dữ liệu trích xuất từ MinIO Parquet:")
                    st.dataframe(df_result, use_container_width=True)
            except Exception:
                pass

            st.markdown("#### 💡 Nhận định kinh doanh:")
            st.markdown(explanation)

            st.session_state[session_key].append({
                "role": "assistant",
                "content": explanation,
                "sql": gen_sql,
                "data": df_result
            })