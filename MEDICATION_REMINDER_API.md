# Medication Reminder API Documentation

**Base URL:** `/api/v1/reminders`

**Authentication:** Bearer Token required for all endpoints

---

## Table of Contents
1. [Create Reminder](#1-create-reminder)
2. [Get All Reminders](#2-get-all-reminders)
3. [Get Single Reminder](#3-get-single-reminder)
4. [Update Reminder](#4-update-reminder)
5. [Delete Reminder](#5-delete-reminder)
6. [Toggle Active Status](#6-toggle-active-status)
7. [Get Weekly Calendar](#7-get-weekly-calendar)
8. [Get Daily Schedule](#8-get-daily-schedule)
9. [Toggle Medication Taken](#9-toggle-medication-taken)
10. [Get Adherence Logs](#10-get-adherence-logs)

---

## Data Models

### TimeSchedule Object
```json
{
  "time": "07:00",        // HH:MM format (00:00 - 23:59)
  "period": "morning",    // "morning", "noon", "afternoon", "evening"
  "dosage": "2"          // Number as string (e.g., "2", "1.5")
}
```

### Unit Types
- `Viên` - Tablet
- `Xit` - Spray
- `Ong` - Tube
- `ml` - Milliliter
- `Mieng` - Piece
- `Lieu` - Dose
- `Goi` - Packet
- `Giot` - Drop

### Meal Timing
- `before_meal` - Trước ăn
- `after_meal` - Sau ăn

### Frequency Types
- `daily` - Mỗi ngày
- `weekly` - Hàng tuần (requires `days_of_week`)
- `every_other_day` - Cách ngày
- `specific_days` - Ngày cụ thể trong tuần (requires `days_of_week`)
- `custom` - Tùy chỉnh

### Days of Week
Array of integers: `0` = Monday, `1` = Tuesday, ..., `6` = Sunday

Example: `[0, 2, 4]` = Monday, Wednesday, Friday

---

## 1. Create Reminder

**Endpoint:** `POST /api/v1/reminders/`

**Request Body:**
```json
{
  "medicine_id": 123,                    // Optional: ID from medicines table
  "medicine_name": "Paracetamol 500mg",  // Required
  "dosage": "500mg",                     // Optional: overall dosage info
  "unit": "Viên",                        // Optional
  "meal_timing": "after_meal",           // Optional
  "frequency": "daily",                  // Required
  "times": [                             // Required: at least 1
    {
      "time": "07:00",
      "period": "morning",
      "dosage": "2"
    },
    {
      "time": "19:00",
      "period": "evening",
      "dosage": "2"
    }
  ],
  "days_of_week": null,                  // Required for "weekly" or "specific_days"
  "start_date": "2025-12-02",           // Required: YYYY-MM-DD
  "end_date": "2025-12-10",             // Optional: YYYY-MM-DD
  "is_notification_enabled": true,       // Optional: default true
  "notes": "Uống sau ăn 30 phút"        // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "user_id": 123,
  "medicine_id": 123,
  "medicine_name": "Paracetamol 500mg",
  "dosage": "500mg",
  "unit": "Viên",
  "meal_timing": "after_meal",
  "frequency": "daily",
  "times": [
    {
      "time": "07:00",
      "period": "morning",
      "dosage": "2"
    },
    {
      "time": "19:00",
      "period": "evening",
      "dosage": "2"
    }
  ],
  "days_of_week": null,
  "start_date": "2025-12-02",
  "end_date": "2025-12-10",
  "is_active": true,
  "is_notification_enabled": true,
  "notes": "Uống sau ăn 30 phút",
  "created_at": "2025-12-02T08:00:00",
  "updated_at": null,
  "is_custom_medicine": false
}
```

**Example: Weekly Reminder**
```json
{
  "medicine_name": "Vitamin D3",
  "unit": "Viên",
  "frequency": "weekly",
  "days_of_week": [1, 3, 5],  // Tuesday, Thursday, Saturday
  "times": [
    {
      "time": "09:00",
      "period": "morning",
      "dosage": "1"
    }
  ],
  "start_date": "2025-12-02"
}
```

**Example: Every Other Day**
```json
{
  "medicine_name": "Calcium",
  "unit": "Viên",
  "frequency": "every_other_day",
  "times": [
    {
      "time": "20:00",
      "period": "evening",
      "dosage": "1"
    }
  ],
  "start_date": "2025-12-02"
}
```

**Error Cases:**
- `400 Bad Request`: Invalid data (missing required fields, invalid time format, etc.)
- `404 Not Found`: If `medicine_id` doesn't exist
- `401 Unauthorized`: Missing or invalid auth token

---

## 2. Get All Reminders

**Endpoint:** `GET /api/v1/reminders/`

**Query Parameters:**
- `skip` (optional): Offset for pagination. Default: `0`
- `limit` (optional): Number of items. Default: `50`, Max: `100`
- `is_active` (optional): Filter by active status. Values: `true`, `false`

**Examples:**
```bash
GET /api/v1/reminders/
GET /api/v1/reminders/?skip=0&limit=20
GET /api/v1/reminders/?is_active=true
```

**Response:** `200 OK`
```json
{
  "reminders": [
    {
      "id": 1,
      "user_id": 123,
      "medicine_name": "Paracetamol 500mg",
      "frequency": "daily",
      "times": [...],
      // ... other fields
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

**Error Cases:**
- `401 Unauthorized`: Missing or invalid auth token

---

## 3. Get Single Reminder

**Endpoint:** `GET /api/v1/reminders/{reminder_id}`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 123,
  "medicine_name": "Paracetamol 500mg",
  "dosage": "500mg",
  "unit": "Viên",
  "meal_timing": "after_meal",
  "frequency": "daily",
  "times": [...],
  // ... complete reminder object
}
```

**Error Cases:**
- `404 Not Found`: Reminder doesn't exist or doesn't belong to user
- `401 Unauthorized`: Missing or invalid auth token

---

## 4. Update Reminder

**Endpoint:** `PUT /api/v1/reminders/{reminder_id}`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Request Body:** (All fields optional)
```json
{
  "dosage": "1000mg",
  "unit": "Viên",
  "meal_timing": "before_meal",
  "times": [
    {
      "time": "08:00",
      "period": "morning",
      "dosage": "1"
    }
  ],
  "end_date": "2025-12-20",
  "is_active": true,
  "is_notification_enabled": false,
  "notes": "Updated notes"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  // ... updated reminder object
}
```

**Error Cases:**
- `404 Not Found`: Reminder doesn't exist or doesn't belong to user
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Missing or invalid auth token

---

## 5. Delete Reminder

**Endpoint:** `DELETE /api/v1/reminders/{reminder_id}`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Response:** `200 OK`
```json
{
  "message": "Reminder deleted successfully"
}
```

**Error Cases:**
- `404 Not Found`: Reminder doesn't exist or doesn't belong to user
- `401 Unauthorized`: Missing or invalid auth token

---

## 6. Toggle Active Status

**Endpoint:** `POST /api/v1/reminders/{reminder_id}/toggle`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Response:** `200 OK`
```json
{
  "id": 1,
  "is_active": false,  // Toggled value
  // ... complete reminder object
}
```

**Behavior:**
- If `is_active = true`, sets to `false`
- If `is_active = false`, sets to `true`

**Error Cases:**
- `404 Not Found`: Reminder doesn't exist or doesn't belong to user
- `401 Unauthorized`: Missing or invalid auth token

---

## 7. Get Weekly Calendar

**Endpoint:** `GET /api/v1/reminders/calendar`

**Query Parameters:**
- `week_offset` (optional): Week offset from current week. Default: `0`
  - `0`: This week (Monday - Sunday)
  - `-1`: Last week
  - `1`: Next week

**Examples:**
```bash
GET /api/v1/reminders/calendar              # This week
GET /api/v1/reminders/calendar?week_offset=-1  # Last week
GET /api/v1/reminders/calendar?week_offset=1   # Next week
```

**Response:** `200 OK`
```json
{
  "start_date": "2025-12-02",  // Monday
  "end_date": "2025-12-08",    // Sunday
  "days": [
    {
      "date": "2025-12-02",
      "has_reminders": true,
      "reminder_count": 4,
      "times": ["07:00", "12:00", "18:00", "21:00"]
    },
    {
      "date": "2025-12-03",
      "has_reminders": true,
      "reminder_count": 3,
      "times": ["07:00", "12:00", "21:00"]
    },
    // ... 7 days total (Mon-Sun)
  ]
}
```

**Use Cases:**
- Display calendar view in mobile app
- Show which days have medications
- Show total medication count per day

**Error Cases:**
- `401 Unauthorized`: Missing or invalid auth token

---

## 8. Get Daily Schedule

**Endpoint:** `GET /api/v1/reminders/calendar/{date}`

**Path Parameters:**
- `date`: Date in YYYY-MM-DD format

**Examples:**
```bash
GET /api/v1/reminders/calendar/2025-12-02
```

**Response:** `200 OK`
```json
{
  "date": "2025-12-02",
  "total_reminders": 4,
  "schedules": [
    {
      "reminder_id": 1,
      "medicine_name": "Paracetamol 500mg",
      "time": "07:00",
      "dosage": "2 Viên",
      "unit": "Viên",
      "meal_timing": "after_meal",
      "period": "morning",
      "status": "taken",
      "is_taken": true
    },
    {
      "reminder_id": 2,
      "medicine_name": "Vitamin D3",
      "time": "09:00",
      "dosage": "1 Viên",
      "unit": "Viên",
      "meal_timing": "before_meal",
      "period": "morning",
      "status": "not_taken",
      "is_taken": false
    },
    {
      "reminder_id": 1,
      "medicine_name": "Paracetamol 500mg",
      "time": "19:00",
      "dosage": "2 Viên",
      "unit": "Viên",
      "meal_timing": "after_meal",
      "period": "evening",
      "status": "not_taken",
      "is_taken": false
    }
  ]
}
```

**Status Values:**
- `not_taken`: Chưa uống
- `taken`: Đã uống

**Use Cases:**
- Display daily timeline of medications
- Show medication details with dosage and timing
- Filter by taken/not_taken status

**Error Cases:**
- `400 Bad Request`: Invalid date format
- `401 Unauthorized`: Missing or invalid auth token

---

## 9. Toggle Medication Taken

**Endpoint:** `POST /api/v1/reminders/{reminder_id}/toggle-taken`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Request Body:** Empty (no body required)

**Behavior:**
1. Automatically finds the **most recent medication time that has passed** today
2. Toggles taken status for that time:
   - If not taken → marks as taken
   - If taken → marks as not taken

**Example Scenario:**
```
Current time: 13:30
Reminder times: 07:00, 12:00, 18:00

API call → Toggles status for 12:00 (most recent past time)
```

**Response:** `200 OK`

**When marking as TAKEN:**
```json
{
  "id": 5,
  "reminder_id": 1,
  "user_id": 123,
  "scheduled_time": "2025-12-02T12:00:00",
  "action_time": "2025-12-02T13:30:15",
  "action_type": "taken",
  "snooze_minutes": null,
  "created_at": "2025-12-02T13:30:15"
}
```

**When marking as NOT TAKEN:**
```json
{
  "id": 0,
  "reminder_id": 1,
  "user_id": 123,
  "scheduled_time": "2025-12-02T12:00:00",
  "action_time": null,
  "action_type": "not_taken",
  "snooze_minutes": null,
  "created_at": "2025-12-02T13:30:15"
}
```

**Error Cases:**

**400 Bad Request - No time has passed:**
```json
{
  "detail": "No medication time has passed yet today"
}
```
Example: Current time is 06:30, first medication is at 07:00

**400 Bad Request - Not scheduled today:**
```json
{
  "detail": "No medication scheduled for today"
}
```
Example: Reminder is "weekly" on Mon/Wed/Fri, but today is Tuesday

**400 Bad Request - Reminder not active:**
```json
{
  "detail": "Reminder is not active today"
}
```
Example: Reminder start_date is in the future or end_date has passed

**404 Not Found:**
```json
{
  "detail": "Reminder not found"
}
```

**Use Cases:**
- User clicks checkbox to mark medication as taken
- User unchecks to mark as not taken
- Simple toggle - no need to specify which time
- Works only after medication time has passed

---

## 10. Get Adherence Logs

**Endpoint:** `GET /api/v1/reminders/{reminder_id}/adherence`

**Path Parameters:**
- `reminder_id`: ID of the reminder

**Query Parameters:**
- `limit` (optional): Max number of logs. Default: `100`, Max: `500`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "reminder_id": 1,
    "user_id": 123,
    "scheduled_time": "2025-12-02T07:00:00",
    "action_time": "2025-12-02T07:15:00",
    "action_type": "taken",
    "snooze_minutes": null,
    "created_at": "2025-12-02T07:15:00"
  },
  {
    "id": 2,
    "reminder_id": 1,
    "user_id": 123,
    "scheduled_time": "2025-12-02T19:00:00",
    "action_time": "2025-12-02T19:05:00",
    "action_type": "taken",
    "snooze_minutes": null,
    "created_at": "2025-12-02T19:05:00"
  }
]
```

**Use Cases:**
- View medication adherence history
- Calculate adherence rate
- Show medication taking timeline

**Error Cases:**
- `404 Not Found`: Reminder doesn't exist or doesn't belong to user
- `401 Unauthorized`: Missing or invalid auth token

---

## Common Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Reminder not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "times", 0, "time"],
      "msg": "Invalid time format: 25:00. Use HH:MM format (00:00-23:59)",
      "type": "value_error"
    }
  ]
}
```

---

## Typical Mobile App Workflows

### 1. Create Daily Medication Reminder
```
1. User fills form with medication details
2. POST /api/v1/reminders/ with complete data
3. Show success message
4. Refresh reminders list
```

### 2. View Today's Medications
```
1. GET /api/v1/reminders/calendar/{today_date}
2. Display list sorted by time
3. Show taken/not_taken status
4. Allow user to toggle each medication
```

### 3. Mark Medication as Taken
```
1. User clicks checkbox/button
2. POST /api/v1/reminders/{id}/toggle-taken
3. Update UI with new status
4. Show confirmation
```

### 4. View Weekly Calendar
```
1. GET /api/v1/reminders/calendar?week_offset=0
2. Display Mon-Sun grid
3. Show medication count per day
4. Allow navigation to prev/next week (week_offset -1/+1)
```

### 5. Edit Reminder
```
1. GET /api/v1/reminders/{id} to load current data
2. User modifies fields
3. PUT /api/v1/reminders/{id} with updated data
4. Show success message
```

---

## Notes for Mobile Developers

1. **Authentication:** All endpoints require `Authorization: Bearer {token}` header

2. **Date Format:** Always use `YYYY-MM-DD` for dates

3. **Time Format:** Always use `HH:MM` (24-hour format) for times

4. **Backward Compatibility:** Old reminders may have simple time strings instead of TimeSchedule objects. The API automatically converts them.

5. **Toggle Taken Logic:** The API is smart - it finds the right medication time automatically. Just call the endpoint, no need to specify which time.

6. **Frequency Types:** Make sure to include `days_of_week` when using "weekly" or "specific_days" frequency.

7. **Pagination:** Use `skip` and `limit` parameters for large datasets.

8. **Error Handling:** Always check for 400, 401, 404 error codes and display appropriate messages.

9. **Timezone:** All times are in server timezone (Vietnam/Ho Chi Minh, UTC+7).

10. **Partial Updates:** For PUT requests, only include fields you want to update. Other fields remain unchanged.
