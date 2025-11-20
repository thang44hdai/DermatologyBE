import sys
import os
# Thêm thư mục hiện tại vào path để import được module app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session, joinedload
from app.db.session import SessionLocal
from app.models.database import Medicines 
from app.models.database import Brand     

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CẤU HÌNH ---
VECTOR_DB_PATH = "faiss_index_store"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def fetch_data_from_db():
    """
    Thay vì gọi API, ta mở kết nối DB trực tiếp
    """
    db: Session = SessionLocal()
    try:
        # Query trực tiếp qua SQLAlchemy với eager loading cho brand relationship
        # Điều này sẽ load brand cùng lúc với medicines, tránh DetachedInstanceError
        medicines = db.query(Medicines).options(joinedload(Medicines.brand)).all() 
        
        print(f"Đã query được {len(medicines)} thuốc từ MySQL.")
        return medicines
    except Exception as e:
        print(f"❌ Lỗi DB: {e}")
        return []
    finally:
        db.close()

def prepare_documents(medicines_list):
    documents = []
    for item in medicines_list:
        # item bây giờ là Object SQLAlchemy, truy cập bằng dấu chấm (.)
        
        # Xử lý quan hệ (nếu Brand là relationship)
        # Brand đã được eager load nên không bị DetachedInstanceError
        brand_name = item.brand.name if item.brand else "Không rõ"
        
        # Lấy ảnh đầu tiên (giả sử images là list JSON hoặc string)
        # Tùy vào cách bạn lưu trong DB mà xử lý
        image_url = ""
        if hasattr(item, 'images') and item.images:
             # Giả sử logic lấy ảnh ở đây
             image_url = str(item.images[0]) if isinstance(item.images, list) else str(item.images)

        # Tạo nội dung vector
        content_text = (
            f"Tên thuốc: {item.name}. "
            f"Tên gốc: {item.generic_name}. "
            f"Thương hiệu: {brand_name}. "
            f"Công dụng: {item.description}. "
            f"Cách dùng: {item.dosage}. "
            f"Tác dụng phụ: {item.side_effects}."
        )
        
        metadata = {
            "medicine_id": item.id, # ID từ DB
            "name": item.name,
            "price": float(item.price) if item.price else 0,
            "image_url": image_url,
            "source": "Direct_MySQL"
        }
        
        doc = Document(page_content=content_text, metadata=metadata)
        documents.append(doc)
    
    return documents

def build_vector_db():
    print("🚀 Bắt đầu tạo Vector DB từ MySQL trực tiếp...")

    # 1. Lấy dữ liệu từ DB
    raw_data = fetch_data_from_db()
    if not raw_data: return

    # 2. Convert sang Document
    documents = prepare_documents(raw_data)

    # 3. Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    splitted_docs = text_splitter.split_documents(documents)

    # 4. Embedding & Save
    print(f"🧠 Đang tải model embedding & tạo Index...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    db = FAISS.from_documents(splitted_docs, embeddings)
    
    db.save_local(VECTOR_DB_PATH)
    print(f"✅ Hoàn tất! Vector DB đã lưu tại '{VECTOR_DB_PATH}'")

if __name__ == "__main__":
    build_vector_db()