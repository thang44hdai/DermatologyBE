"""
Medication Reminder Schemas

Pydantic models for medication reminder API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date


class ReminderCreate(BaseModel):
    """Schema for creating a new medication reminder"""
    medicine_id: Optional[int] = Field(None, description="Medicine ID from database (optional)")
    medicine_name: str = Field(..., min_length=1, max_length=255, description="Medicine name (required)")
    title: str = Field(..., min_length=1, max_length=255, description="Reminder title")
    dosage: Optional[str] = Field(None, max_length=100, description="Dosage (e.g., 500mg, 2 viên)")
    frequency: str = Field(..., description="Frequency: daily, weekly, or custom")
    times: List[str] = Field(..., min_length=1, description="Array of times in HH:MM format")
    days_of_week: Optional[List[int]] = Field(None, description="For weekly: 0-6 (Monday-Sunday)")
    start_date: date = Field(..., description="Start date for reminder")
    end_date: Optional[date] = Field(None, description="Optional end date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('medicine_name')
    @classmethod
    def validate_medicine_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Medicine name cannot be empty')
        return v.strip()
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = ['daily', 'weekly', 'custom']
        if v not in valid:
            raise ValueError(f'Frequency must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('times')
    @classmethod
    def validate_times(cls, v: List[str]) -> List[str]:
        import re
        time_pattern = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        for time_str in v:
            if not time_pattern.match(time_str):
                raise ValueError(f'Invalid time format: {time_str}. Use HH:MM format (00:00-23:59)')
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
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    times: Optional[List[str]] = Field(None, min_length=1)
    days_of_week: Optional[List[int]] = Field(None)
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    
    @field_validator('times')
    @classmethod
    def validate_times(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            import re
            time_pattern = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
            for time_str in v:
                if not time_pattern.match(time_str):
                    raise ValueError(f'Invalid time format: {time_str}')
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
    title: str
    dosage: Optional[str]
    frequency: str
    times: List[str]
    days_of_week: Optional[List[int]]
    start_date: date
    end_date: Optional[date]
    is_active: bool
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
    """Schema for user action on a reminder"""
    action_type: str = Field(..., description="Action: taken, snoozed, or skipped")
    snooze_minutes: Optional[int] = Field(None, ge=5, le=60, description="Minutes to snooze (5-60)")
    
    @field_validator('action_type')
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid = ['taken', 'snoozed', 'skipped']
        if v not in valid:
            raise ValueError(f'Action type must be one of: {", ".join(valid)}')
        return v
    
    @field_validator('snooze_minutes')
    @classmethod
    def validate_snooze(cls, v: Optional[int], info) -> Optional[int]:
        data = info.data
        if data.get('action_type') == 'snoozed' and not v:
            raise ValueError('snooze_minutes required for snoozed action')
        return v


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
