import os
import sys
from dotenv import load_dotenv

# Đảm bảo nhận diện được thư mục gốc của project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Đảm bảo in Unicode (emoji) không bị lỗi trên Windows Terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
from config.metadata_definitions import METADATA_CHUNKS

# 1. Nạp API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")

# Cấu hình trực tiếp cho SDK Gemini
genai.configure(api_key=api_key)

# 2. Định nghĩa Custom Embedding Function tương thích chuẩn ChromaDB
class GeminiCustomEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str = "models/gemini-embedding-001"):
        self.model_name = model_name

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            res = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(res["embedding"])
        return embeddings

# 3. Khởi tạo Persistent Client lưu vector vào thư mục data/vector_db
print("⏳ Khởi tạo ChromaDB client...")
persist_dir = os.path.join("data", "vector_db")
client = chromadb.PersistentClient(path=persist_dir)

# 4. Tạo hoặc lấy Collection với Custom Embedding Function
collection_name = "lakehouse_metadata"
gemini_ef = GeminiCustomEmbeddingFunction()

collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=gemini_ef,
    metadata={"description": "Metadata và Rules của E-commerce Lakehouse"}
)

# 5. Đẩy dữ liệu vào ChromaDB
print("⏳ Đang tạo Embeddings qua Gemini API và nạp vào ChromaDB...")
ids = [chunk["id"] for chunk in METADATA_CHUNKS]
documents = [chunk["content"] for chunk in METADATA_CHUNKS]
metadatas = [{"title": chunk["title"], "type": chunk["type"]} for chunk in METADATA_CHUNKS]

collection.upsert(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print(f"✅ Đã index thành công {len(ids)} chunks metadata vào ChromaDB tại: {persist_dir}!")

# 6. Kiểm tra truy vấn Semantic Search
print("\n--- TEST SEMANTIC SEARCH TRÊN CHROMADB ---")
test_query = "Hãng laptop nào có giá rẻ nhất?"
print(f"Câu hỏi thử nghiệm: '{test_query}'")

results = collection.query(
    query_texts=[test_query],
    n_results=2
)

for i, doc in enumerate(results["documents"][0]):
    doc_id = results["ids"][0][i]
    print(f"\n[Kết quả {i+1} - ID: {doc_id}]")
    print(doc.strip()[:200] + "...")