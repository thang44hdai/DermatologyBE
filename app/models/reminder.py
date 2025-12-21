from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class MedicationReminder(Base):
    """
    Medication reminders for users
    
    Supports both medicines from database and custom user-entered medicines.
    """
    __tablename__ = "medication_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)  # Optional: for DB medicines
    medicine_name = Column(String(255), nullable=False)  # Required: custom or from DB
    dosage = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)  # Viên, Xit, Ong, ml, Mieng, Lieu, Goi, Giot
    meal_timing = Column(String(20), nullable=True)  # before_meal, after_meal
    frequency = Column(String(50), nullable=False)  # 'daily', 'weekly', 'every_other_day', 'specific_days', 'custom'
    times = Column(Text, nullable=False)  # JSON array of times: ["08:00", "14:00", "20:00"]
    days_of_week = Column(Text, nullable=True)  # JSON array for weekly: [0,1,2,3,4,5,6]
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_notification_enabled = Column(Boolean, default=True, nullable=False)  # Notification toggle
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="medication_reminders")
    medicine = relationship("Medicines")  # Optional relationship
    adherence_logs = relationship("AdherenceLog", back_populates="reminder", cascade="all, delete-orphan")

class AdherenceLog(Base):
    """
    Adherence tracking for medication reminders
    
    Tracks when users take, snooze, or skip their medications.
    """
    __tablename__ = "adherence_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("medication_reminders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    action_time = Column(DateTime, nullable=True)
    action_type = Column(String(20), nullable=False)  # 'taken', 'snoozed', 'skipped'
    snooze_minutes = Column(Integer, nullable=True)  # For snoozed actions (5-60 minutes)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    reminder = relationship("MedicationReminder", back_populates="adherence_logs")
    user = relationship("User")
