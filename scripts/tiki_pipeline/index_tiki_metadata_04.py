import os
import sys
from dotenv import load_dotenv

# Thêm thư mục gốc vào path để import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
from config.metadata_tiki_definitions import TIKI_METADATA_CHUNKS

# 1. Cấu hình Gemini API
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")

genai.configure(api_key=api_key)

# 2. Embedding Function dùng Gemini text-embedding-004
class GeminiCustomEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str = "models/text-embedding-004"):
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

def main():
    print("🚀 Khởi chạy Indexing Metadata cho Tiki Books...")
    
    # Lưu vector database vào data/vector_db_tiki/
    persist_dir = os.path.join("data", "vector_db_tiki")
    client = chromadb.PersistentClient(path=persist_dir)
    
    collection = client.get_or_create_collection(
        name="tiki_lakehouse_metadata",
        embedding_function=GeminiCustomEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"}
    )
    
    ids = [chunk["id"] for chunk in TIKI_METADATA_CHUNKS]
    documents = [chunk["content"] for chunk in TIKI_METADATA_CHUNKS]
    metadatas = [{"title": chunk["title"]} for chunk in TIKI_METADATA_CHUNKS]
    
    print("⏳ Đang tạo Embeddings qua Gemini API và nạp vào ChromaDB...")
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✅ Đã index thành công {len(ids)} chunks metadata vào ChromaDB tại: {persist_dir}")

    # Test Semantic Search
    test_query = "Tìm các cuốn sách bán chạy nhất của thể loại tiểu thuyết"
    print(f"\n--- TEST SEMANTIC SEARCH: '{test_query}' ---")
    results = collection.query(query_texts=[test_query], n_results=1)
    print(f"ID tìm thấy: {results['ids'][0][0]}")
    print("Nội dung trích xuất:")
    print(results['documents'][0][0][:250] + "...")

if __name__ == "__main__":
    main()