import os
import sys
import re
from typing import TypedDict, Optional
from dotenv import load_dotenv

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
from langgraph.graph import StateGraph, END

# Import Semantic Layer của Tiki Books
from scripts.tiki_pipeline.semantic_tiki_03 import get_duckdb_tiki_lakehouse

# 1. Cấu hình Gemini API
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")

genai.configure(api_key=api_key)
llm = genai.GenerativeModel("models/gemini-flash-lite-latest")

# 2. Embedding Function cho ChromaDB
class GeminiCustomEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str = "models/gemini-embedding-001"):
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            res = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query"
            )
            embeddings.append(res["embedding"])
        return embeddings

# Kết nối ChromaDB Tiki Metadata
persist_dir = os.path.join("data", "vector_db_tiki")
client = chromadb.PersistentClient(path=persist_dir)
collection = client.get_collection(
    name="tiki_lakehouse_metadata",
    embedding_function=GeminiCustomEmbeddingFunction()
)

# Kết nối DuckDB Semantic Layer Tiki Books
duckdb_tiki_con = get_duckdb_tiki_lakehouse()

# 3. Định nghĩa State của Agent
class AgentState(TypedDict):
    user_query: str
    retrieved_context: str
    generated_sql: str
    query_result: Optional[str]
    error_message: Optional[str]
    final_answer: str
    retry_count: int

import time
from google.api_core.exceptions import ResourceExhausted

CANDIDATE_MODELS = [
    "models/gemini-flash-lite-latest",
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.7-flash",
]

def generate_content_with_retry(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                return model.generate_content(prompt)
            except ResourceExhausted:
                continue
            except Exception as e:
                continue
        wait_time = 20
        print(f"⚠️ Các mô hình Gemini đều chạm giới hạn quota. Đang chờ {wait_time}s thử lại...", flush=True)
        time.sleep(wait_time)
    raise RuntimeError("❌ Không thể gọi Gemini API sau khi thử tất cả mô hình dự phòng.")

# --- NODE 1: RETRIEVAL CONTEXT ---
def retrieve_context_node(state: AgentState) -> dict:
    query = state["user_query"]
    results = collection.query(query_texts=[query], n_results=2)
    context = "\n\n".join(results["documents"][0])
    return {"retrieved_context": context}

# --- NODE 2: GENERATE SQL (Text-to-SQL) ---
def generate_sql_node(state: AgentState) -> dict:
    error_feedback = ""
    if state.get("error_message"):
        error_feedback = f"""
        LƯU Ý LỖI: Câu SQL trước đó bị lỗi cú pháp thực thi như sau:
        {state['error_message']}
        Hãy sửa lỗi và tạo lại câu truy vấn chính xác.
        """

    prompt = f"""
Bạn là chuyên gia Data Engineer viết câu truy vấn DuckDB SQL cho bộ dữ liệu Tiki Books Lakehouse.
Dựa vào ngữ cảnh Metadata và quy tắc nghiệp vụ sau:
{state['retrieved_context']}

{error_feedback}

Yêu cầu phân tích từ người dùng: "{state['user_query']}"

QUY TẮC BẮT BUỘC:
1. Chỉ truy vấn từ duy nhất bảng view: `semantic_tiki_book_insights`.
2. Không tự bịa tên cột. Dùng đúng tên cột từ metadata:
   book_id, book_title, authors, category, manufacturer, pages,
   current_price, original_price, discount_amount, discount_percentage,
   quantity_sold, estimated_revenue, avg_rating, review_count.
3. Khi tìm kiếm theo tên hoặc tác giả, ưu tiên dùng `ILIKE '%...%'`.
4. CHỈ TRẢ VỀ CÂU TRUY VẤN SQL DUY NHẤT trong khối mã ```sql ... ```. Không giải thích thêm.
"""
    response = generate_content_with_retry(prompt)
    raw_text = response.text
    sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_text, re.DOTALL)
    sql_query = sql_match.group(1).strip() if sql_match else raw_text.strip()
    return {"generated_sql": sql_query}

# --- NODE 3: EXECUTE SQL (DuckDB Engine) ---
def execute_sql_node(state: AgentState) -> dict:
    sql = state["generated_sql"]
    try:
        df = duckdb_tiki_con.execute(sql).df()
        if df.empty:
            result_str = "Không tìm thấy dữ liệu nào phù hợp."
        else:
            result_str = df.to_string(index=False)
        return {"query_result": result_str, "error_message": None}
    except Exception as e:
        return {
            "query_result": None,
            "error_message": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

# --- NODE 4: EXPLAIN RESULT ---
def explain_result_node(state: AgentState) -> dict:
    prompt = f"""
Bạn là trợ lý BI & Data Analyst thông minh, chuyên phân tích thị trường sách Tiki.
Người dùng hỏi: "{state['user_query']}"

Câu lệnh SQL đã chạy trên Lakehouse:
{state['generated_sql']}

Dữ liệu kết quả thu được:
{state['query_result']}

Hãy đưa ra câu trả lời súc tích, chuyên nghiệp bằng tiếng Việt:
- Trả lời thẳng vào trọng tâm câu hỏi.
- Nêu rõ các con số thống kê (giá VNĐ, số lượng bán, doanh thu, đánh giá).
- Đưa ra nhận xét ngắn về xu hướng kinh doanh nếu có.
"""
    response = generate_content_with_retry(prompt)
    return {"final_answer": response.text}

# --- CONDITIONAL ROUTING (SELF-CORRECTION) ---
def should_retry(state: AgentState) -> str:
    if state.get("error_message") and state.get("retry_count", 0) < 3:
        print(f"⚠️ SQL lỗi, Agent đang tự sửa (Lần {state.get('retry_count')}): {state.get('error_message')}")
        return "generate_sql"
    return "explain_result"

# 4. Xây dựng StateGraph
workflow = StateGraph(AgentState)
workflow.add_node("retrieve_context", retrieve_context_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("explain_result", explain_result_node)

workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", should_retry, {
    "generate_sql": "generate_sql",
    "explain_result": "explain_result"
})
workflow.add_edge("explain_result", END)

tiki_agent_app = workflow.compile()

if __name__ == "__main__":
    print("\n🤖 Tiki Books Multi-Agent đã sẵn sàng!\n")
    test_q = "Top 3 cuốn sách tiểu thuyết có doanh thu ước tính cao nhất?"
    print(f"❓ Câu hỏi test: {test_q}")
    out = tiki_agent_app.invoke({"user_query": test_q, "retry_count": 0, "error_message": None})
    print(f"\n🛠️ SQL Generated:\n{out['generated_sql']}")
    print(f"\n📊 Dữ liệu:\n{out['query_result']}")
    print(f"\n💡 Phân tích:\n{out['final_answer']}")