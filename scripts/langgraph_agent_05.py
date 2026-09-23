import os
import sys
import re
from typing import TypedDict, Optional
from dotenv import load_dotenv

# Đảm bảo in Unicode (emoji) không bị lỗi trên Windows Terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Đảm bảo import được các module từ thư mục gốc
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
from langgraph.graph import StateGraph, END

# Import trực tiếp hàm get_duckdb_lakehouse từ semantic_layer_03
from scripts.semantic_layer_03 import get_duckdb_lakehouse

# --- CẤU HÌNH HỆ THỐNG ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")

genai.configure(api_key=api_key)
llm = genai.GenerativeModel("models/gemini-3.6-flash")

# Custom Embedding Function khớp với vector DB đã index ở Pha 3
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

# Kết nối ChromaDB
persist_dir = os.path.join("data", "vector_db")
client = chromadb.PersistentClient(path=persist_dir)
collection = client.get_collection(
    name="lakehouse_metadata",
    embedding_function=GeminiCustomEmbeddingFunction()
)

# Kết nối DuckDB Semantic Layer
duckdb_con = get_duckdb_lakehouse()

# --- ĐỊNH NGHĨA TRẠNG THÁI (AGENT STATE) ---
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

def generate_content_with_retry(llm, prompt, max_retries=10):
    for attempt in range(max_retries):
        try:
            return llm.generate_content(prompt)
        except ResourceExhausted as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = 60
            print(f"⚠️ Chạm giới hạn Gemini API (Rate Limit 429). Tự động chờ {wait_time}s để reset quota...", flush=True)
            time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️ Lỗi tạm thời khi gọi Gemini API ({e}). Thử lại sau 5s...", flush=True)
            time.sleep(5)

# --- NODE 1: RETRIEVE METADATA CONTEXT ---
def retrieve_context_node(state: AgentState) -> dict:
    print("  [Step 1] Đang tìm kiếm Metadata từ ChromaDB...", flush=True)
    query = state["user_query"]
    results = collection.query(query_texts=[query], n_results=2)
    context = "\n\n".join(results["documents"][0])
    return {"retrieved_context": context}

# --- NODE 2: GENERATE SQL (TEXT-TO-SQL) ---
def generate_sql_node(state: AgentState) -> dict:
    print("  [Step 2] Đang tạo SQL truy vấn qua Gemini...", flush=True)
    error_feedback = ""
    if state.get("error_message"):
        error_feedback = f"""
        LƯU Ý: Câu truy vấn trước đó bị lỗi cú pháp thực thi như sau:
        {state['error_message']}
        Hãy phân tích lỗi trên và viết lại câu lệnh SQL chuẩn xác hơn.
        """

    prompt = f"""
Bạn là chuyên gia Data Engineer viết truy vấn DuckDB SQL cho hệ thống Data Lakehouse.
Dựa vào ngữ cảnh Metadata và quy tắc nghiệp vụ sau:
{state['retrieved_context']}

{error_feedback}

Yêu cầu phân tích từ người dùng: "{state['user_query']}"

QUY TẮC BẮT BUỘC:
1. Chỉ truy vấn trên view ngữ nghĩa duy nhất: `semantic_daily_product_insights`.
2. Không bịa đặt tên cột ngoài danh sách metadata.
3. Chỉ trả về mã SQL nằm trong khối mã ```sql ... ```. Không giải thích thêm.
"""
    response = generate_content_with_retry(llm, prompt)
    raw_text = response.text
    
    # Trích xuất đoạn SQL bên trong markdown
    sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", raw_text, re.DOTALL)
    sql_query = sql_match.group(1).strip() if sql_match else raw_text.strip()
    return {"generated_sql": sql_query}

# --- NODE 3: EXECUTE SQL (DUCKDB ENGINE) ---
def execute_sql_node(state: AgentState) -> dict:
    print("  [Step 3] Đang thực thi SQL trên DuckDB Lakehouse...", flush=True)
    sql = state["generated_sql"]
    try:
        df = duckdb_con.execute(sql).df()
        if df.empty:
            result_str = "Không tìm thấy bản ghi nào khớp với điều kiện lọc."
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
    print("  [Step 4] Đang phân tích và tổng hợp câu trả lời...", flush=True)
    prompt = f"""
Bạn là trợ lý BI / Data Analyst chuyên nghiệp.
Người dùng đặt câu hỏi: "{state['user_query']}"

Câu lệnh SQL đã chạy trên Lakehouse:
{state['generated_sql']}

Dữ liệu thô thu được từ kho:
{state['query_result']}

Hãy trình bày câu trả lời ngắn gọn, nêu rõ con số, làm nổi bật thông tin nghiệp vụ và đưa ra nhận xét súc tích bằng tiếng Việt.
"""
    response = generate_content_with_retry(llm, prompt)
    return {"final_answer": response.text}

# --- CƠ CHẾ RẼ NHÁNH TỰ SỬA LỖI (CONDITIONAL ROUTING) ---
def should_retry(state: AgentState) -> str:
    if state.get("error_message") and state.get("retry_count", 0) < 3:
        print(f"⚠️ SQL thực thi lỗi, đang yêu cầu Agent sửa lại (Lần thử {state.get('retry_count')}): {state.get('error_message')}")
        return "generate_sql"
    return "explain_result"

# --- BIÊN DỊCH ĐỒ THỊ LANGGRAPH ---
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

agent_app = workflow.compile()

# --- CHẠY THỬ NGHIỆM TƯƠNG TÁC ---
if __name__ == "__main__":
    print("\n🤖 Hệ thống LangGraph Text-to-SQL Analytics đã khởi động!\n")
    
    test_questions = [
        "Thương hiệu nào có giá bán trung bình cao nhất?",
        "Top 3 tai nghe có tỷ lệ giảm giá nhiều nhất"
    ]
    
    for q in test_questions:
        print("\n" + "=" * 50, flush=True)
        print(f"❓ Câu hỏi: {q}", flush=True)
        
        initial_state = {
            "user_query": q,
            "retry_count": 0,
            "error_message": None
        }
        
        output = agent_app.invoke(initial_state)
        
        print(f"\n[1] 🛠️ DuckDB SQL được sinh ra:", flush=True)
        print(output['generated_sql'], flush=True)
        
        print(f"\n[2] 📊 Kết quả truy vấn từ MinIO Parquet:", flush=True)
        print(output['query_result'], flush=True)
        
        print(f"\n[3] 💡 Phân tích từ Trợ lý AI:", flush=True)
        print(output['final_answer'], flush=True)
        
        time.sleep(3)