# 🔬 PREDICTION API - UPDATED DOCUMENTATION

## 📋 Overview

API Prediction đã được cập nhật để tích hợp với database mới:
- Lưu scan history vào database
- Liên kết với diagnosis records
- Hỗ trợ xem lịch sử và chi tiết scan
- Yêu cầu authentication cho tất cả endpoints

---

## 🚀 API Endpoints

### Base URL
```
http://localhost:8000/api/v1/prediction
```

**⚠️ Tất cả endpoints yêu cầu Authentication:** Bearer token in Authorization header

---

## 1️⃣ **Predict Disease** (Chẩn đoán bệnh)

### `POST /api/v1/prediction/predict`

Upload ảnh để AI chẩn đoán bệnh da.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (Form Data):**
```
file: <image_file>
```

**Supported Formats:**
- JPG, JPEG, PNG, BMP, GIF, TIFF, WEBP

**Max File Size:** 5MB (configurable)

**Response (200 OK):**
```json
{
  "success": true,
  "label_en": "Acne and Rosacea Photos",
  "label_vi": "Mụn trứng cá và Rosacea",
  "confidence": 0.856,
  "all_predictions": [
    {
      "label_en": "Acne and Rosacea Photos",
      "label_vi": "Mụn trứng cá và Rosacea",
      "confidence": 0.856
    },
    {
      "label_en": "Eczema Photos",
      "label_vi": "Chàm (Eczema)",
      "confidence": 0.089
    }
  ],
  "scan_id": 1,
  "diagnosis_id": 5,
  "user_id": 1
}
```

**Process Flow:**
1. Validate image format and size
2. Run AI model prediction
3. Find or create diagnosis record in database
4. Save scan record with user_id, diagnosis_id, confidence
5. Return prediction with IDs for tracking

**Curl Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/prediction/predict" \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@skin_image.jpg"
```

---

## 2️⃣ **Get Scan History** (Lịch sử chẩn đoán)

### `GET /api/v1/prediction/history`

Xem lịch sử các lần chẩn đoán của user hiện tại.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (int, optional): Số lượng bỏ qua (pagination), default = 0
- `limit` (int, optional): Số lượng tối đa trả về (max 100), default = 20

**Response (200 OK):**
```json
{
  "total": 5,
  "skip": 0,
  "limit": 20,
  "scans": [
    {
      "scan_id": 5,
      "image_url": "skin_photo.jpg",
      "confidence": 0.92,
      "scan_date": "2025-10-24T14:30:00.000Z",
      "diagnosis": {
        "id": 3,
        "disease_name": "Eczema Photos",
        "description": "AI-detected: Chàm (Eczema)",
        "severity_level": "medium"
      }
    },
    {
      "scan_id": 4,
      "image_url": "another_image.jpg",
      "confidence": 0.85,
      "scan_date": "2025-10-23T10:15:00.000Z",
      "diagnosis": {
        "id": 5,
        "disease_name": "Acne and Rosacea Photos",
        "description": "AI-detected: Mụn trứng cá và Rosacea",
        "severity_level": "medium"
      }
    }
  ]
}
```

**Curl Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prediction/history?skip=0&limit=10" \
  -H "Authorization: Bearer <your_token>"
```

---

## 3️⃣ **Get Scan Detail** (Chi tiết scan)

### `GET /api/v1/prediction/scan/{scan_id}`

Xem thông tin chi tiết của một lần chẩn đoán.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `scan_id` (int, required): ID của scan record

**Response (200 OK):**
```json
{
  "scan_id": 5,
  "user_id": 1,
  "image_url": "skin_photo.jpg",
  "ai_model_version": "1.0",
  "confidence": 0.92,
  "scan_date": "2025-10-24T14:30:00.000Z",
  "diagnosis": {
    "id": 3,
    "disease_name": "Eczema Photos",
    "description": "AI-detected: Chàm (Eczema)",
    "symptoms": null,
    "treatment": null,
    "severity_level": "medium",
    "created_at": "2025-10-24T14:30:00.000Z"
  }
}
```

**Error Responses:**
- `404 Not Found` - Scan không tồn tại hoặc không thuộc về user hiện tại

**Curl Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prediction/scan/5" \
  -H "Authorization: Bearer <your_token>"
```

---

## 4️⃣ **Delete Scan** (Xóa scan)

### `DELETE /api/v1/prediction/scan/{scan_id}`

Xóa một scan record khỏi lịch sử.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `scan_id` (int, required): ID của scan record cần xóa

**Response (200 OK):**
```json
{
  "message": "Scan deleted successfully",
  "scan_id": 5
}
```

**Error Responses:**
- `404 Not Found` - Scan không tồn tại hoặc không thuộc về user hiện tại

**Curl Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/prediction/scan/5" \
  -H "Authorization: Bearer <your_token>"
```

---

## 🗄️ Database Schema

### Tables Used

#### **scans**
```sql
- id (PK)
- user_id (FK → users.id)
- image_url (VARCHAR 500)
- ai_model_version (VARCHAR 50)
- diagnosis_id (FK → diagnoses.id)
- confidence (FLOAT)
- scan_date (DATETIME)
```

#### **diagnoses**
```sql
- id (PK)
- disease_name (VARCHAR 255)
- description (TEXT)
- symptoms (TEXT)
- treatment (TEXT)
- severity_level (VARCHAR 50)
- created_at (DATETIME)
```

#### **user_diagnosis_history**
```sql
- id (PK)
- user_id (FK → users.id)
- diagnosis_id (FK → diagnoses.id)
- scan_id (FK → scans.id)
- notes (TEXT)
- created_at (DATETIME)
```

---

## 🔄 Workflow Example

### Complete Prediction Flow

```bash
# 1. Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Upload image for prediction
curl -X POST "http://localhost:8000/api/v1/prediction/predict" \
  -H "Authorization: Bearer eyJ..." \
  -F "file=@my_skin_photo.jpg"

# Response: 
# {
#   "success": true,
#   "label_vi": "Mụn trứng cá và Rosacea",
#   "confidence": 0.856,
#   "scan_id": 15,
#   "diagnosis_id": 5,
#   ...
# }

# 3. View prediction history
curl -X GET "http://localhost:8000/api/v1/prediction/history" \
  -H "Authorization: Bearer eyJ..."

# 4. Get detailed info about a specific scan
curl -X GET "http://localhost:8000/api/v1/prediction/scan/15" \
  -H "Authorization: Bearer eyJ..."

# 5. Delete a scan if needed
curl -X DELETE "http://localhost:8000/api/v1/prediction/scan/15" \
  -H "Authorization: Bearer eyJ..."
```

---

## 📊 Changes from Old API

### ✅ New Features

1. **Database Integration**
   - Scans are now saved to database
   - Linked to diagnosis records
   - Full history tracking

2. **New Endpoints**
   - `GET /history` - View all scans
   - `GET /scan/{id}` - Scan details
   - `DELETE /scan/{id}` - Remove scan

3. **Enhanced Response**
   - Returns `scan_id`, `diagnosis_id`, `user_id`
   - Full diagnosis information

4. **Authentication Required**
   - All endpoints now require Bearer token
   - User-specific data isolation

### 🔄 Updated

- **Prediction endpoint** now saves to database automatically
- **Response schema** includes additional IDs for tracking
- **User association** - each scan belongs to a user

### ⚠️ Breaking Changes

- Authentication is now **required** (was optional before)
- Response includes new fields: `scan_id`, `diagnosis_id`, `user_id`

---

## 🧪 Testing with Swagger UI

1. **Login first**: Use `/api/v1/auth/login` or `/api/v1/auth/register`
2. **Copy token** from response
3. **Click "Authorize"** in Swagger UI (top right)
4. **Paste token** and click Authorize
5. **Test prediction**: Upload image at `/api/v1/prediction/predict`
6. **View history**: Check `/api/v1/prediction/history`
7. **View details**: Use scan_id from prediction to get details

---

## ⚠️ Error Codes

| Code | Endpoint | Meaning |
|------|----------|---------|
| 400 | /predict | Unsupported file type or file too large |
| 401 | All | Invalid or missing authentication token |
| 404 | /scan/{id} | Scan not found or doesn't belong to user |
| 500 | /predict | Error processing image or running AI model |

---

## 🔐 Security

✅ **User Isolation**: Users can only see/delete their own scans  
✅ **Authentication**: All endpoints require valid JWT token  
✅ **File Validation**: Extension and content type checking  
✅ **Size Limits**: Max upload size enforcement  
✅ **SQL Injection Protection**: SQLAlchemy ORM  

---

## 📝 Notes

### Image Storage
Currently `image_url` stores the filename. In production:
- Upload to cloud storage (S3, Azure Blob, etc.)
- Store full URL in database
- Implement image retrieval endpoint

### Diagnosis Records
- Auto-created on first prediction for each disease
- Reused for subsequent predictions of same disease
- Can be enhanced with symptoms, treatment info

### Future Enhancements
- Image upload to cloud storage
- Image retrieval endpoint
- Confidence threshold alerts
- Diagnosis statistics
- Export history to PDF

---

**Server:** http://localhost:8000  
**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc
