"""
Medication Reminder Schemas

Pydantic models for medication reminder API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, date


class TimeSchedule(BaseModel):
    """Detailed time schedule with period and dosage"""
    time: str = Field(..., description="Time in HH:MM format")
    period: str = Field(..., description="morning, noon, afternoon, evening")
    dosage: str = Field(..., description="Number of units (e.g., '2', '1.5')")
    
    @field_validator('time')
    @classmethod
    def validate_time(cls, v: str) -> str:
        import re
        time_pattern = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        if not time_pattern.match(v):
            raise ValueError(f'Invalid time format: {v}. Use HH:MM format (00:00-23:59)')
        return v
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        valid = ['morning', 'noon', 'afternoon', 'evening']
        if v not in valid:
            raise ValueError(f'Period must be one of: {", ".join(valid)}')
        return v


class ReminderCreate(BaseModel):
    """Schema for creating a new medication reminder"""
    medicine_id: Optional[int] = Field(None, description="Medicine ID from database (optional)")
    medicine_name: str = Field(..., min_length=1, max_length=255, description="Medicine name (required)")
    dosage: Optional[str] = Field(None, max_length=100, description="Dosage (e.g., 500mg, 2 viên)")
    unit: Optional[str] = Field(None, max_length=50, description="Unit: Viên, Xit, Ong, ml, Mieng, Lieu, Goi, Giot")
    meal_timing: Optional[str] = Field(None, description="Meal timing: before_meal or after_meal")
    frequency: str = Field(..., description="Frequency: daily, weekly, every_other_day, specific_days, or custom")
    times: List[TimeSchedule] = Field(..., min_length=1, description="Time schedules with period and dosage")
    days_of_week: Optional[List[int]] = Field(None, description="For weekly/specific_days: 0-6 (Monday-Sunday)")
    start_date: date = Field(..., description="Start date for reminder")
    end_date: Optional[date] = Field(None, description="Optional end date")
    is_notification_enabled: bool = Field(default=True, description="Enable push notifications")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('medicine_name')
    @classmethod
    def validate_medicine_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Medicine name cannot be empty')
        return v.strip()
    
    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ['Viên', 'Xịt', 'Ống', 'ml', 'Miếng', 'Liều', 'Gói', 'Giọt']
            if v not in valid:
                raise ValueError(f'Unit must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('meal_timing')
    @classmethod
    def validate_meal_timing(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ['before_meal', 'after_meal']
            if v not in valid:
                raise ValueError(f'Meal timing must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = ['daily', 'weekly', 'every_other_day', 'specific_days', 'custom']
        if v not in valid:
            raise ValueError(f'Frequency must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('days_of_week')
    @classmethod
    def validate_days_of_week(cls, v: Optional[List[int]], info) -> Optional[List[int]]:
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError('Days of week must be 0-6 (0=Monday, 6=Sunday)')
            return sorted(list(set(v)))
        return v


class ReminderUpdate(BaseModel):
    """Schema for updating a medication reminder"""
    dosage: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    meal_timing: Optional[str] = Field(None)
    times: Optional[List[TimeSchedule]] = Field(None, min_length=1)
    days_of_week: Optional[List[int]] = Field(None)
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_notification_enabled: Optional[bool] = None
    notes: Optional[str] = None
    
    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ['Viên', 'Xit', 'Ong', 'ml', 'Mieng', 'Lieu', 'Goi', 'Giot']
            if v not in valid:
                raise ValueError(f'Unit must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('meal_timing')
    @classmethod
    def validate_meal_timing(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ['before_meal', 'after_meal']
            if v not in valid:
                raise ValueError(f'Meal timing must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('days_of_week')
    @classmethod
    def validate_days_of_week(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError('Days of week must be 0-6')
            return sorted(list(set(v)))
        return v


class ReminderResponse(BaseModel):
    """Schema for reminder response"""
    id: int
    user_id: int
    medicine_id: Optional[int]
    medicine_name: str
    dosage: Optional[str]
    unit: Optional[str]
    meal_timing: Optional[str]
    frequency: str
    times: List[dict]  # Dict representation of TimeSchedule
    days_of_week: Optional[List[int]]
    start_date: date
    end_date: Optional[date]
    is_active: bool
    is_notification_enabled: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_custom_medicine: bool = Field(..., description="True if medicine_id is null")
    
    class Config:
        from_attributes = True


class ReminderListResponse(BaseModel):
    """Schema for paginated reminder list"""
    reminders: List[ReminderResponse]
    total: int
    skip: int
    limit: int


class AdherenceAction(BaseModel):
    """Schema for toggling medication taken status"""
    # No fields needed - it's just a toggle
    pass


class AdherenceLogResponse(BaseModel):
    """Schema for adherence log response"""
    id: int
    reminder_id: int
    user_id: int
    scheduled_time: datetime
    action_time: Optional[datetime]
    action_type: str
    snooze_minutes: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdherenceStats(BaseModel):
    """Schema for monthly adherence statistics"""
    month: str = Field(..., description="Month in YYYY-MM format")
    total_scheduled: int = Field(..., ge=0)
    total_taken: int = Field(..., ge=0)
    total_snoozed: int = Field(..., ge=0)
    total_skipped: int = Field(..., ge=0)
    adherence_rate: float = Field(..., ge=0, le=100, description="Percentage (0-100)")


class AdherenceChartData(BaseModel):
    """Schema for daily adherence chart data"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    taken: int = Field(..., ge=0)
    snoozed: int = Field(..., ge=0)
    skipped: int = Field(..., ge=0)


class AIAdvice(BaseModel):
    """AI-generated personalized advice based on adherence behavior"""
    medicine_name: str = Field(..., description="Medicine name")
    advice_text: str = Field(..., description="Personalized advice paragraph")
    adherence_rate: float = Field(..., description="Current adherence rate (%)")
    total_logs: int = Field(..., description="Total adherence logs")


class AIAdviceRequest(BaseModel):
    """Request schema for AI advice"""
    medicine_name: str = Field(..., min_length=1, max_length=255)


# Calendar View Schemas

class CalendarDaySchedule(BaseModel):
    """Schedule for a single day"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    has_reminders: bool = Field(..., description="True if any reminders on this day")
    reminder_count: int = Field(..., description="Total reminders scheduled")
    times: List[str] = Field(..., description="All scheduled times (HH:MM)")


class CalendarMonthOverview(BaseModel):
    """30-day calendar overview (15 days before + 15 days after today)"""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD")
    end_date: str = Field(..., description="End date in YYYY-MM-DD")
    days: List[CalendarDaySchedule] = Field(..., description="Daily schedules")


class ReminderScheduleItem(BaseModel):
    """Single reminder schedule item"""
    reminder_id: int
    medicine_name: str
    time: str = Field(..., description="Time in HH:MM format")
    dosage: Optional[str]
    is_taken: bool = Field(..., description="Whether medicine has been taken")
    unit: Optional[str] = Field(None, description="Unit (Viên, Xịt, etc.)")
    meal_timing: Optional[str] = Field(None, description="before_meal or after_meal")
    note: Optional[str] = Field(None, description="Additional notes")
    period: Optional[str] = Field(None, description="morning, afternoon, evening, night")


class DailyScheduleDetail(BaseModel):
    """Detailed schedule for a specific day"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    total_reminders: int = Field(..., description="Total reminders scheduled")
    schedules: List[ReminderScheduleItem] = Field(..., description="Reminder schedule items")
