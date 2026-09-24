import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

# Thêm thư mục gốc vào path để import agent
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from scripts.langgraph_agent_05 import agent_app, duckdb_con

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="Lakehouse Text-to-SQL Analytics",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ E-Commerce Data Lakehouse AI Agent")
st.caption("Kiến trúc MinIO (S3 Parquet) + DuckDB Semantic Layer + Metadata RAG (ChromaDB) + LangGraph Multi-Agent (Gemini)")

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: Khám phá nhanh dữ liệu Semantic Layer
with st.sidebar:
    st.header("📊 Semantic Layer Overview")
    st.write("Bảng view: `semantic_daily_product_insights`")
    
    if st.button("Tải lại mẫu dữ liệu (5 dòng)"):
        try:
            preview_df = duckdb_con.execute(
                "SELECT product_name, brand, category_name, current_price, discount_percentage FROM semantic_daily_product_insights LIMIT 5;"
            ).df()
            st.dataframe(preview_df)
        except Exception as e:
            st.error(f"Lỗi truy vấn: {e}")
            
    st.divider()
    st.markdown("""
    **Gợi ý câu hỏi:**
    - *Thương hiệu nào có tỷ lệ giảm giá trung bình cao nhất?*
    - *Top 5 sản phẩm có lượt đánh giá cao nhất của hãng Apple.*
    - *Giá trung bình của từng ngành hàng là bao nhiêu?*
    """)

# Hiển thị các tin nhắn cũ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg and msg["data"] is not None:
            st.dataframe(msg["data"])

# Xử lý input từ người dùng
user_input = st.chat_input("Nhập câu hỏi phân tích dữ liệu kinh doanh...")

if user_input:
    # 1. Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Xử lý qua LangGraph Agent
    with st.chat_message("assistant"):
        with st.spinner("Agent đang tra cứu metadata, sinh SQL và quét Lakehouse..."):
            initial_state = {
                "user_query": user_input,
                "retry_count": 0,
                "error_message": None
            }
            output = agent_app.invoke(initial_state)
            
            gen_sql = output.get("generated_sql", "")
            raw_result = output.get("query_result", "")
            explanation = output.get("final_answer", "")

            # Hiển thị câu SQL đã tạo
            st.markdown("#### 🛠️ Câu lệnh SQL thực thi:")
            st.code(gen_sql, language="sql")

            # Lấy DataFrame từ DuckDB để hiển thị bảng & biểu đồ
            df_result = None
            try:
                df_result = duckdb_con.execute(gen_sql).df()
                if not df_result.empty:
                    st.markdown("#### 📋 Dữ liệu trích xuất từ MinIO:")
                    st.dataframe(df_result, use_container_width=True)
            except Exception:
                pass

            # Hiển thị giải thích nghiệp vụ của Gemini
            st.markdown("#### 💡 Nhận định kinh doanh:")
            st.markdown(explanation)

            # Lưu vào session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": explanation,
                "sql": gen_sql,
                "data": df_result
            })