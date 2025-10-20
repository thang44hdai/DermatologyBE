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

### 4. Cấu hình môi trường

```bash
# Copy file .env.example thành .env
copy .env.example .env

# Chỉnh sửa .env với cấu hình của bạn
```

### 5. Di chuyển model file

```bash
# Di chuyển file model vào thư mục đúng
move skin_disease_model.pth resources\models\skin_disease_fusion_model_final.pth
```

### 6. Chạy ứng dụng

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

### Prediction
- `POST /api/v1/prediction/predict` - Chẩn đoán bệnh da từ ảnh

### Users (CRUD)
- `POST /api/v1/users/` - Tạo user mới
- `GET /api/v1/users/{user_id}` - Lấy thông tin user
- `GET /api/v1/users/` - Lấy danh sách users
- `DELETE /api/v1/users/{user_id}` - Xóa user

## 🧪 Testing

```bash
# Chạy tests
pytest tests/

# Với coverage
pytest --cov=app tests/
```

## 📝 Ví dụ sử dụng

### Predict Disease

```python
import requests

url = "http://localhost:8000/api/v1/prediction/predict"
files = {'file': open('skin_image.jpg', 'rb')}
response = requests.post(url, files=files)
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

Mặc định sử dụng SQLite cho development. Để chuyển sang PostgreSQL:

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
