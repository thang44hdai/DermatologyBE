# PharmaAI - Backend API

**Đồ án tốt nghiệp Đại học** | Học viện Công nghệ Bưu chính Viễn thông (PTIT)

**Điểm số: 8.8/10**

---

## Giới thiệu

PharmaAI là hệ thống hỗ trợ chẩn đoán bệnh da liễu và tư vấn dược phẩm sử dụng trí tuệ nhân tạo. Backend API được xây dựng trên nền tảng FastAPI, tích hợp các mô hình học sâu (Deep Learning) cho việc phân loại bệnh da và chatbot RAG (Retrieval-Augmented Generation) sử dụng LLM để tư vấn thuốc.

Hệ thống cung cấp các chức năng chính:
- Phân loại bệnh da liễu từ hình ảnh sử dụng mô hình CNN
- Chatbot tư vấn dược phẩm với RAG + LLM (Qwen3-4B fine-tuned)
- Quản lý thuốc, nhà thuốc, thương hiệu và danh mục
- Nhắc nhở uống thuốc với push notification
- Xác thực đăng nhập bằng Google/Facebook OAuth2
- Real-time chat qua WebSocket

---

## Các thành phần hệ thống

Dự án PharmaAI bao gồm nhiều repository liên quan:

| Repository | Mô tả | Công nghệ |
|------------|-------|-----------|
| **DermatologyBE** (repo này) | Backend API chính | FastAPI, SQLAlchemy, PyTorch |
| **PharmaAI-Mobile** | Ứng dụng Android | Kotlin, Jetpack Compose, Retrofit |
| **SkinDisease-Classification** | Fine-tune model phân loại ảnh bệnh da | PyTorch, EfficientNet, Transfer Learning |
| **PharmaAI-LLM** | Fine-tune model Qwen3-4B chatbot | LLaMA.cpp, LoRA, Hugging Face |

---

## Kiến trúc hệ thống

```
                                    +------------------+
                                    |   Mobile App     |
                                    |   (Android)      |
                                    +--------+---------+
                                             |
                                             | HTTPS/WSS
                                             v
+------------------+              +----------+---------+              +------------------+
|   Firebase       |<----------->|   Nginx Proxy      |<------------>|   LLM Server     |
|   - Storage      |              |   Manager (SSL)    |              |   (Qwen3-4B)     |
|   - FCM          |              +----------+---------+              +------------------+
+------------------+                         |
                                             v
                              +-----------------------------+
                              |      FastAPI Backend        |
                              |  +------------------------+ |
                              |  |   AI Service           | |
                              |  |   - Skin Classification| |
                              |  |   - RAG Chat Service   | |
                              |  +------------------------+ |
                              |  +------------------------+ |
                              |  |   Business Logic       | |
                              |  |   - Medicine, Pharmacy | |
                              |  |   - Reminders, Auth    | |
                              |  +------------------------+ |
                              +-------------+--------------+
                                            |
                        +-------------------+-------------------+
                        v                                       v
              +-----------------+                     +-----------------+
              |     MySQL       |                     |     Redis       |
              |   (Database)    |                     |   (Cache)       |
              +-----------------+                     +-----------------+
```

---

## Công nghệ sử dụng

**Backend Framework**
- FastAPI - Web framework hiệu năng cao
- SQLAlchemy - ORM cho database
- Pydantic - Data validation và serialization

**AI/ML**
- PyTorch - Deep learning framework
- LangChain - Framework cho LLM applications
- FAISS - Vector similarity search
- HuggingFace Transformers - Pre-trained models

**Database & Cache**
- MySQL 8.0 - Relational database
- Redis - Caching và rate limiting

**Infrastructure**
- Docker & Docker Compose - Containerization
- Nginx Proxy Manager - Reverse proxy với SSL
- Firebase - Storage và Push Notification

**Authentication**
- JWT (JSON Web Tokens)
- OAuth2 (Google, Facebook)
- bcrypt - Password hashing

---

## Cấu trúc thư mục

```
DermatologyBE/
├── app/
│   ├── api/v1/endpoints/      # API endpoints
│   │   ├── auth.py            # Authentication
│   │   ├── prediction.py      # AI skin prediction
│   │   ├── chat.py            # RAG chatbot
│   │   ├── medicines.py       # Medicine management
│   │   ├── pharmacy.py        # Pharmacy management
│   │   ├── reminders.py       # Medication reminders
│   │   └── users.py           # User management
│   ├── config/                # Configuration
│   ├── core/                  # Core utilities
│   │   ├── dependencies.py    # Dependency injection
│   │   ├── security.py        # JWT & OAuth2
│   │   └── websocket_manager.py
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── ai_service.py      # AI prediction
│   │   ├── chat_service.py    # RAG chatbot
│   │   ├── medicine_service.py
│   │   ├── notification_service.py
│   │   └── scheduler_service.py
│   ├── utils/                 # Utilities
│   │   ├── firebase_storage.py
│   │   └── file_upload.py
│   └── main.py                # Application entry
├── resources/
│   └── models/                # AI model weights
├── faiss_index_store/         # Vector database
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── requirements-cpu.txt       # CPU-only dependencies
```

---

## Hướng dẫn cài đặt

### Yêu cầu hệ thống

- Python 3.11+
- MySQL 8.0+
- Redis (optional, for caching)
- CUDA 11.8+ (optional, for GPU inference)

### Cài đặt môi trường phát triển

**1. Clone repository**

```bash
git clone https://github.com/your-username/DermatologyBE.git
cd DermatologyBE
```

**2. Tạo virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**3. Cài đặt dependencies**

```bash
# CPU only (recommended for development)
pip install -r requirements-cpu.txt

# With CUDA support
pip install -r requirements.txt
```

**4. Cấu hình biến môi trường**

```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/dermatology_db

# Security
SECRET_KEY=your-secret-key-change-in-production

# Firebase
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json

# LLM Server (optional)
LLM_SERVER_URL=http://localhost:8080/v1

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

**5. Khởi tạo database**

```bash
# Tạo database trong MySQL
mysql -u root -p -e "CREATE DATABASE dermatology_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Tables sẽ được tạo tự động khi chạy ứng dụng
```

**6. Thêm model AI**

Copy file model vào thư mục:
```bash
cp skin_disease_fusion_model_final.pth resources/models/
```

**7. Build Vector Database (cho chatbot)**

```bash
python build_vector_db.py
```

**8. Chạy ứng dụng**

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Truy cập API documentation: http://localhost:8000/docs

---

## Hướng dẫn Deploy

### Deploy với Docker (Production)

**1. Chuẩn bị server**

- Ubuntu 22.04 LTS
- Docker và Docker Compose
- Domain với SSL certificate

**2. Clone và cấu hình**

```bash
git clone https://github.com/your-username/DermatologyBE.git
cd DermatologyBE

# Tạo file .env
cp .env.example .env
nano .env
```

**3. Thêm Firebase credentials**

```bash
# Upload firebase-service-account.json lên server
scp firebase-service-account.json user@server:~/DermatologyBE/
```

**4. Build và chạy**

```bash
# Build image
docker compose build

# Start services
docker compose up -d

# Xem logs
docker compose logs -f app
```

**5. Cấu hình Nginx Proxy Manager**

Truy cập `http://your-server-ip:81` để cấu hình:
- Domain name
- SSL certificate (Let's Encrypt)
- WebSocket support

**6. Khởi tạo database**

```bash
# Import data (optional)
docker cp backup.sql dermatology_mysql:/tmp/
docker compose exec mysql sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" dermatology_db < /tmp/backup.sql'

# Tạo admin user
docker cp create_admin.py dermatology_app:/app/
docker compose exec app python create_admin.py
```

### Docker Compose Services

```yaml
services:
  nginx-proxy:      # Reverse proxy với SSL
  app:              # FastAPI application
  mysql:            # MySQL database
  redis:            # Redis cache
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/auth/register` | Đăng ký tài khoản |
| POST | `/auth/login` | Đăng nhập |
| POST | `/auth/google` | Đăng nhập với Google |
| POST | `/auth/refresh` | Refresh access token |

### AI Prediction
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/prediction/predict` | Phân loại bệnh da từ ảnh |
| GET | `/prediction/history` | Lịch sử chẩn đoán |

### Chatbot
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/chat/` | Gửi tin nhắn chat |
| WebSocket | `/chat/ws` | Real-time chat |
| GET | `/chat/sessions` | Danh sách phiên chat |

### Medicine & Pharmacy
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/medicines/` | Danh sách thuốc |
| GET | `/pharmacies/` | Danh sách nhà thuốc |
| GET | `/pharmacies/nearby/search` | Tìm nhà thuốc gần đây |

### User Profile
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/users/me` | Thông tin profile |
| PUT | `/users/me` | Cập nhật profile và avatar |

---

## Bảo mật

- JWT authentication với access/refresh tokens
- Password hashing sử dụng bcrypt
- CORS middleware cho cross-origin requests
- Rate limiting để chống DDoS
- Input validation với Pydantic
- File upload validation (type, size)

---

## Tác giả

**Nguyen Quang Thang**

**Bui Hai Nam**

Sinh viên Học viện Công nghệ Bưu chính Viễn thông (PTIT)

Khoa Công nghệ Thông tin

Niên khóa 2021-2025

---

## Giấy phép

Dự án này được phát triển cho mục đích học thuật và nghiên cứu.

Copyright 2025 - Học viện Công nghệ Bưu chính Viễn thông (PTIT)
