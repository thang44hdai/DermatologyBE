from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    fullname = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    gender = Column(String(10), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    fcm_token = Column(String(255), nullable=True)  # Firebase Cloud Messaging token
    oauth_provider = Column(String(20), nullable=True)  # google, facebook, or null
    google_id = Column(String(255), nullable=True, unique=True)  # Google user ID
    facebook_id = Column(String(255), nullable=True, unique=True)  # Facebook user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scans = relationship("Scans", back_populates="user")
    diagnosis_history = relationship("DiagnosisHistory", back_populates="user")
    notifications = relationship("Notifications", back_populates="user")
    app_logs = relationship("AppLogs", back_populates="user")
    chat_sessions = relationship("ChatSessions", back_populates="user")
    medication_reminders = relationship("MedicationReminder", back_populates="user")

class AppLogs(Base):
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    ip_address = Column(String(50), nullable=True)
    device_info = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="app_logs")

class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=0)
    created_at = Column(DateTime, server_default=func.now())
    type = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
