import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

# Thêm thư mục gốc vào path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from scripts.mock_pipeline.langgraph_agent_05 import agent_app as mock_agent_app, duckdb_con as mock_duckdb_con
from scripts.tiki_pipeline.langgraph_tiki_agent_05 import tiki_agent_app, duckdb_tiki_con

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="Data Lakehouse AI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại, sang trọng, màu sắc hài hòa dễ nhìn
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* App Background & Padding */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(20, 30, 48, 0.4) 0%, rgba(11, 15, 23, 1) 90%);
}

/* Hero Header */
.hero-container {
    padding: 1.5rem 1.75rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
    backdrop-filter: blur(12px);
}

.hero-title {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.35;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.hero-icon {
    font-size: 2.2rem;
    filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.6));
}

.gradient-text {
    background: linear-gradient(120deg, #ffffff 0%, #c7d2fe 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    padding-top: 2px;
    padding-bottom: 4px;
}

.hero-badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.85rem;
}

.tech-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.28);
    color: #c7d2fe;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
}

.tech-badge:hover {
    background: rgba(99, 102, 241, 0.22);
    border-color: rgba(99, 102, 241, 0.45);
    color: #ffffff;
}

/* Status Cards */
.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.status-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.status-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    font-weight: 600;
}

.status-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #0d1320;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-card {
    background: rgba(30, 41, 59, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 0.85rem;
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
}

.pulse-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    }
    70% {
        transform: scale(1);
        box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
    }
    100% {
        transform: scale(0.95);
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
}

/* Chat Messages */
div[data-testid="stChatMessage"] {
    background-color: rgba(30, 41, 59, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
    background: rgba(49, 46, 129, 0.25);
    border: 1px solid rgba(99, 102, 241, 0.3);
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 600;
    padding: 8px 16px;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(56, 189, 248, 0.15) 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(99, 102, 241, 0.4) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: #6366f1;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

/* Welcome Card */
.welcome-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.6) 100%);
    border: 1px dashed rgba(99, 102, 241, 0.35);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Helper function để vẽ biểu đồ tự động
def render_smart_chart(df: pd.DataFrame):
    """Tự động phân tích dataframe và vẽ biểu đồ Plotly hiện đại nếu phù hợp."""
    if df is None or df.empty or len(df) < 2:
        return None
    
    # Tìm cột chuỗi và cột số
    num_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    str_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    if not num_cols or not str_cols:
        return None
    
    # Ưu tiên các cột số đo lường kinh doanh
    priority_metrics = ["estimated_revenue", "quantity_sold", "avg_rating", "current_price", "discount_percentage"]
    metric_col = next((c for c in priority_metrics if c in num_cols), num_cols[0])
    
    # Ưu tiên cột nhãn
    priority_labels = ["book_title", "authors", "product_name", "brand", "category", "category_name"]
    label_col = next((c for c in priority_labels if c in str_cols), str_cols[0])
    
    # Chuẩn bị dữ liệu hiển thị top 10
    plot_df = df.copy()
    plot_df[label_col] = plot_df[label_col].astype(str)
    
    # Rút ngắn nhãn nếu quá dài
    plot_df["display_label"] = plot_df[label_col].apply(lambda x: x[:35] + "..." if len(x) > 35 else x)
    plot_df = plot_df.sort_values(by=metric_col, ascending=True).tail(10)
    
    fig = px.bar(
        plot_df,
        x=metric_col,
        y="display_label",
        orientation="h",
        text=metric_col,
        labels={"display_label": label_col.replace("_", " ").title(), metric_col: metric_col.replace("_", " ").title()},
        title=f"📊 Biểu đồ so sánh: {metric_col.replace('_', ' ').title()} theo {label_col.replace('_', ' ').title()}"
    )
    
    fig.update_traces(
        marker_color="#6366f1",
        marker_line_color="#38bdf8",
        marker_line_width=1.5,
        opacity=0.9,
        texttemplate='%{text:,.2s}',
        textposition='outside'
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=40, t=50, b=20),
        height=340,
        font=dict(family="Plus Jakarta Sans", color="#94a3b8"),
        title_font=dict(size=14, color="#f8fafc", family="Plus Jakarta Sans"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(showgrid=False)
    )
    return fig

# Sidebar: Lựa chọn Dataset & Điều khiển
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ Lakehouse Control Center</div>', unsafe_allow_html=True)
    
    dataset_mode = st.radio(
        "Nguồn dữ liệu hoạt động:",
        ["Tiki Books (Real Dataset)", "Mock E-Commerce (Synthetic)"],
        index=0,
        help="Chuyển đổi giữa bộ dữ liệu sách thực tế và dữ liệu thương mại điện tử mô phỏng"
    )

    if dataset_mode == "Tiki Books (Real Dataset)":
        active_agent = tiki_agent_app
        active_con = duckdb_tiki_con
        view_name = "semantic_tiki_book_insights"
        sample_query = "SELECT book_title, authors, category, current_price, quantity_sold, estimated_revenue, avg_rating FROM semantic_tiki_book_insights LIMIT 5;"
        suggested_queries = [
            "Top 5 cuốn sách tiểu thuyết có doanh thu ước tính cao nhất?",
            "Thể loại sách nào có điểm đánh giá trung bình cao nhất?",
            "Top 3 cuốn sách giảm giá nhiều nhất của tác giả Nguyễn Nhật Ánh.",
            "Tác giả nào có tổng doanh thu ước tính cao nhất?"
        ]
    else:
        active_agent = mock_agent_app
        active_con = mock_duckdb_con
        view_name = "semantic_daily_product_insights"
        sample_query = "SELECT product_name, brand, category_name, current_price, discount_percentage FROM semantic_daily_product_insights LIMIT 5;"
        suggested_queries = [
            "Thương hiệu nào có tỷ lệ giảm giá trung bình cao nhất?",
            "Top 5 sản phẩm có lượt đánh giá cao nhất của hãng Apple.",
            "Ngành hàng nào có số lượng sản phẩm phong phú nhất?",
            "Top 5 sản phẩm giá cao nhất trong hệ thống."
        ]

    # Status box
    st.markdown(f"""
    <div class="sidebar-card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 0.75rem; color: #94a3b8; font-weight: 600;">TRẠNG THÁI VIEW</span>
            <span style="display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #34d399; font-weight: 600;">
                <span class="pulse-dot"></span> Live Ready
            </span>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #38bdf8; word-break: break-all;">
            {view_name}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clickable suggestions
    st.markdown("**💡 Gợi ý câu hỏi nhanh:**")
    for idx, sq in enumerate(suggested_queries):
        if st.button(f"👉 {sq}", key=f"side_sq_{idx}", use_container_width=True):
            st.session_state["pending_prompt"] = sq

    st.divider()

    # Data preview expander
    with st.expander("🔍 Xem trước mẫu dữ liệu (5 dòng)"):
        if st.button("Tải lại mẫu dữ liệu", use_container_width=True):
            st.session_state[f"preview_{dataset_mode}"] = True
            
        try:
            preview_df = active_con.execute(sample_query).df()
            st.dataframe(preview_df, use_container_width=True, height=200)
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # Xóa lịch sử chat
    session_key = f"messages_{dataset_mode}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []
        
    if st.session_state[session_key]:
        if st.button("🗑️ Xóa lịch sử đoạn chat", use_container_width=True):
            st.session_state[session_key] = []
            st.rerun()

# --- MAIN CONTENT AREA ---

# Hero Header Banner
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">
        <span class="hero-icon">⚡</span>
        <span class="gradient-text">Data Lakehouse AI Analytics Agent</span>
    </h1>
    <div style="color: #94a3b8; font-size: 0.92rem; margin-top: 0.35rem; line-height: 1.5;">
        Trợ lý thông minh phân tích dữ liệu tự động với khả năng dịch ngôn ngữ tự nhiên sang DuckDB SQL và trích xuất trực tiếp từ MinIO S3 Lakehouse.
    </div>
    <div class="hero-badge-container">
        <span class="tech-badge">🗄️ MinIO (S3 Parquet)</span>
        <span class="tech-badge">🦆 DuckDB Semantic Layer</span>
        <span class="tech-badge">🧬 ChromaDB Metadata RAG</span>
        <span class="tech-badge">🦜 LangGraph Multi-Agent</span>
        <span class="tech-badge">✨ Gemini 2.5 Flash</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Status Indicators
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.markdown(f"""
    <div class="status-card">
        <span class="status-label">Dataset hiện tại</span>
        <span class="status-value">📁 {dataset_mode.split(' ')[0]}</span>
    </div>
    """, unsafe_allow_html=True)
with col_s2:
    st.markdown(f"""
    <div class="status-card">
        <span class="status-label">Semantic View</span>
        <span class="status-value" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #38bdf8;">
            {view_name[:18]}...
        </span>
    </div>
    """, unsafe_allow_html=True)
with col_s3:
    st.markdown(f"""
    <div class="status-card">
        <span class="status-label">Lakehouse Engine</span>
        <span class="status-value" style="color: #34d399;">🟢 DuckDB In-Memory</span>
    </div>
    """, unsafe_allow_html=True)
with col_s4:
    total_q = len([m for m in st.session_state[session_key] if m["role"] == "user"])
    st.markdown(f"""
    <div class="status-card">
        <span class="status-label">Số câu đã phân tích</span>
        <span class="status-value" style="color: #a78bfa;">📊 {total_q} truy vấn</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Kiểm tra prompt kích hoạt từ gợi ý hoặc sidebar
prompt_to_run = None
if "pending_prompt" in st.session_state and st.session_state["pending_prompt"]:
    prompt_to_run = st.session_state.pop("pending_prompt")

# Display Empty State if no messages and no pending prompt
if not st.session_state[session_key] and not prompt_to_run:
    st.markdown(f"""
    <div class="welcome-card">
        <h3 style="color: #f8fafc; margin-bottom: 0.5rem; font-size: 1.35rem;">👋 Chào mừng bạn đến với Lakehouse AI Agent</h3>
        <p style="color: #94a3b8; font-size: 0.95rem; max-width: 680px; margin: 0 auto 1.25rem auto; line-height: 1.5;">
            Hệ thống đã kết nối trực tiếp với <strong>{dataset_mode}</strong> qua DuckDB Semantic View.
            Chọn nhanh một câu hỏi phân tích mẫu bên dưới hoặc nhập câu hỏi bất kỳ vào ô chat!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2x2 Grid for Starter Questions
    col_left, col_right = st.columns(2)
    for idx, q_text in enumerate(suggested_queries[:4]):
        target_col = col_left if idx % 2 == 0 else col_right
        with target_col:
            if st.button(f"🎯 {q_text}", key=f"starter_q_{idx}", use_container_width=True):
                st.session_state["pending_prompt"] = q_text
                st.rerun()

# Hiển thị lịch sử chat
for idx, msg in enumerate(st.session_state[session_key]):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"**{msg['content']}**")
        else:
            # Assistant response format
            explanation = msg.get("content", "")
            gen_sql = msg.get("sql", "")
            data_df = msg.get("data", None)

            # Tạo tabs cho câu trả lời
            tab_names = ["💡 Nhận định & Phân tích", "📊 Bảng dữ liệu"]
            has_chart = False
            chart_fig = None
            if data_df is not None and not data_df.empty:
                chart_fig = render_smart_chart(data_df)
                if chart_fig:
                    has_chart = True
                    tab_names.append("📈 Biểu đồ trực quan")
            tab_names.append("🛠️ DuckDB SQL")

            tabs = st.tabs(tab_names)

            # Tab 1: Explanation
            with tabs[0]:
                st.markdown(explanation)

            # Tab 2: Dataframe
            with tabs[1]:
                if data_df is not None and not data_df.empty:
                    col_m1, col_m2 = st.columns([3, 1])
                    with col_m1:
                        st.caption(f"Trích xuất: **{len(data_df)} dòng** × **{len(data_df.columns)} cột**")
                    with col_m2:
                        csv = data_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Tải CSV",
                            data=csv,
                            file_name=f"lakehouse_query_{idx}.csv",
                            mime="text/csv",
                            key=f"dl_csv_{idx}",
                            use_container_width=True
                        )
                    st.dataframe(data_df, use_container_width=True)
                else:
                    st.info("Không có bảng dữ liệu trả về cho truy vấn này.")

            # Tab 3: Chart (if available)
            if has_chart and chart_fig:
                with tabs[2]:
                    st.plotly_chart(chart_fig, use_container_width=True, key=f"chart_{idx}")

            # Last Tab: SQL
            with tabs[-1]:
                if gen_sql:
                    st.code(gen_sql, language="sql")
                else:
                    st.info("Không có mã SQL.")

# Nhận input từ chat_input
user_input = st.chat_input(f"Đặt câu hỏi phân tích cho {dataset_mode}...")
if user_input:
    prompt_to_run = user_input

# Thực thi nếu có prompt
if prompt_to_run:
    # 1. Lưu câu hỏi user vào session
    st.session_state[session_key].append({"role": "user", "content": prompt_to_run})

    # 2. Xử lý phản hồi assistant
    with st.chat_message("user"):
        st.markdown(f"**{prompt_to_run}**")

    with st.chat_message("assistant"):
        with st.spinner("⚡ Đang phân tích metadata, dịch DuckDB SQL và truy xuất MinIO Parquet..."):
            initial_state = {
                "user_query": prompt_to_run,
                "retry_count": 0,
                "error_message": None
            }
            output = active_agent.invoke(initial_state)

            gen_sql = output.get("generated_sql", "")
            explanation = output.get("final_answer", "")

            # Thực thi SQL để lấy DataFrame
            df_result = None
            try:
                df_result = active_con.execute(gen_sql).df()
            except Exception:
                df_result = None

            # Lưu vào session_state và rerun để cập nhật giao diện đồng nhất
            st.session_state[session_key].append({
                "role": "assistant",
                "content": explanation,
                "sql": gen_sql,
                "data": df_result
            })
            st.rerun()