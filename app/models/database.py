from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class UserRole(str, enum.Enum):
    """User role enum"""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and tracking"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    predictions = relationship("PredictionHistory", back_populates="user")


class PredictionHistory(Base):
    """Store prediction history for analytics and tracking"""
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_filename = Column(String(255), nullable=True)
    predicted_label_en = Column(String(100), nullable=False)
    predicted_label_vi = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    all_predictions = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="predictions")
