# Dermatology Backend API

API backend cho hệ thống chẩn đoán bệnh da bằng AI sử dụng FastAPI và Deep Learning.

## 🏗️ Cấu trúc dự án

```
DermatologyBE/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Entry point của ứng dụng
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Cấu hình & biến môi trường
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   └── security.py         # Authentication & security
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ai_model.py         # Định nghĩa model AI
│   │   └── database.py         # Database models (SQLAlchemy)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── prediction.py       # Pydantic schemas cho prediction
│   │   └── user.py             # Pydantic schemas cho user
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── prediction.py   # AI prediction endpoints
│   │       │   ├── users.py        # User CRUD endpoints
│   │       │   └── health.py       # Health check
│   │       └── router.py           # Router tổng hợp
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # Logic xử lý AI prediction
│   │   └── user_service.py     # Business logic cho users
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── image_processing.py # Xử lý ảnh
│   │   └── constants.py        # Constants & mappings
│   └── db/
│       ├── __init__.py
│       └── session.py          # Database session
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── resources/
│   ├── models/
│   │   └── skin_disease_model.pth
│   └── data/
│       └── train_processed.csv
├── .env                        # Environment variables (không commit)
├── .env.example               # Template cho .env
├── .gitignore
├── requirements.txt           # Python dependencies
└── README.md
```

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd DermatologyBE
```

### 2. Tạo virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình Database MySQL với XAMPP

#### Bước 1: Khởi động XAMPP
1. Mở XAMPP Control Panel
2. Start **Apache** và **MySQL**

#### Bước 2: Tạo Database
Có 2 cách để tạo database:

**Cách 1: Sử dụng phpMyAdmin**
1. Mở trình duyệt và truy cập: http://localhost/phpmyadmin
2. Click vào tab "SQL"
3. Copy và paste nội dung từ file `database_setup.sql`
4. Click "Go" để thực thi

**Cách 2: Sử dụng MySQL Command Line**
```bash
# Mở terminal và kết nối MySQL
mysql -u root -p
# (Nhấn Enter nếu không có password)

# Chạy SQL script
source database_setup.sql
```

#### Bước 3: Cấu hình file .env
```bash
# Copy file .env.example thành .env (nếu có)
cp .env.example .env

# File .env đã được cấu hình sẵn với MySQL:
DATABASE_URL=mysql+pymysql://root:@localhost:3306/dermatology_db
```

**Lưu ý:**
- Nếu MySQL của bạn có password, sửa thành: `mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/dermatology_db`
- Nếu MySQL chạy trên port khác 3306, thay đổi port number tương ứng

#### Bước 4: Tạo Tables trong Database
```bash
# Chạy script để tạo tables tự động
python init_db.py

# Nếu muốn xóa và tạo lại tables (CẢNH BÁO: Sẽ mất dữ liệu!)
python init_db.py --drop
```

### 5. Cấu hình môi trường

```bash
# Copy file .env.example thành .env (nếu chưa có)
# File .env đã được cấu hình sẵn, bạn có thể chỉnh sửa nếu cần
```

### 6. Di chuyển model file

```bash
# Di chuyển file model vào thư mục đúng
move skin_disease_model.pth resources\models\skin_disease_fusion_model_final.pth
```

### 7. Chạy ứng dụng

```bash
# Development mode (auto-reload)
python app/main.py

# Hoặc dùng uvicorn trực tiếp
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Sau khi chạy server, truy cập:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔌 API Endpoints

### Health Check
- `GET /api/v1/` - Health check
- `GET /api/v1/health` - Health check (alternative)

### 🔐 Authentication
- `POST /api/v1/auth/register` - Đăng ký user mới
- `POST /api/v1/auth/login` - Đăng nhập (form-data)
- `POST /api/v1/auth/login/json` - Đăng nhập (JSON)
- `GET /api/v1/auth/me` - Lấy thông tin user hiện tại (🔒 Protected)
- `GET /api/v1/auth/test-token` - Test access token (🔒 Protected)

### Prediction
- `POST /api/v1/prediction/predict` - Chẩn đoán bệnh da từ ảnh (🔒 Protected)

### Users (CRUD)
- `POST /api/v1/users/` - Tạo user mới (Public)
- `GET /api/v1/users/{user_id}` - Lấy thông tin user (🔒 Protected)
- `GET /api/v1/users/` - Lấy danh sách users (🔒 Protected)
- `DELETE /api/v1/users/{user_id}` - Xóa user (🔒 Protected)

**🔒 Protected** = Yêu cầu authentication token

## 🔐 Authentication

Hệ thống sử dụng JWT (JSON Web Tokens) để xác thực. Xem chi tiết tại [AUTHENTICATION.md](AUTHENTICATION.md)

### Quick Start với Authentication

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "user@example.com",
        "username": "username",
        "password": "password123"
    }
)
print(response.json())

# 2. Login
response = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"username": "username", "password": "password123"}
)
token_data = response.json()
access_token = token_data["access_token"]

# 3. Use token for protected endpoints
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(response.json())
```

## 🧪 Testing

```bash
# Test Authentication System
python test_auth.py

# Chạy tests
pytest tests/

# Với coverage
pytest --cov=app tests/
```

## 📝 Ví dụ sử dụng

### Complete Flow với Authentication

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login để lấy token
response = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"username": "username", "password": "password123"}
)
access_token = response.json()["access_token"]

# 2. Predict Disease với token
url = f"{BASE_URL}/prediction/predict"
headers = {"Authorization": f"Bearer {access_token}"}
files = {'file': open('skin_image.jpg', 'rb')}
response = requests.post(url, headers=headers, files=files)
print(response.json())
```

Response:
```json
{
  "success": true,
  "label_en": "acne",
  "label_vi": "Mụn trứng cá",
  "confidence": 0.95,
  "all_predictions": [
    {
      "label_en": "acne",
      "label_vi": "Mụn trứng cá",
      "confidence": 0.95
    },
    ...
  ]
}
```

## 🛠️ Technologies

- **FastAPI** - Modern web framework
- **PyTorch** - Deep learning framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

## 🔒 Security

- JWT authentication
- Password hashing với bcrypt
- CORS middleware
- File upload validation

## 📦 Database

### MySQL với XAMPP (Recommended)
Project đã được cấu hình để sử dụng MySQL với XAMPP:

**Cấu hình hiện tại:**
```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/dermatology_db
```

**Tables được tạo tự động:**
- `users` - Quản lý người dùng và authentication
- `prediction_history` - Lưu lịch sử chẩn đoán

**Khởi tạo/Reset Database:**
```bash
# Tạo tables
python init_db.py

# Xóa và tạo lại (CẢNH BÁO: Mất dữ liệu!)
python init_db.py --drop
```

### SQLite (Alternative)
Để chuyển sang SQLite cho development:
```env
DATABASE_URL=sqlite:///./dermatology.db
```

### PostgreSQL (Production)
Để chuyển sang PostgreSQL:
1. Cài đặt: `pip install psycopg2-binary`
2. Cập nhật `DATABASE_URL` trong `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

[Your License Here]

## 👥 Authors

[Your Name]
