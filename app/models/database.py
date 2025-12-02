from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint, Time, Boolean
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


class Scans(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scan_date = Column(DateTime, nullable=False)
    image_url = Column(String(255), nullable=False)
    status = Column(String(50), nullable=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="scans")
    disease = relationship("Disease", back_populates="scans")
    diagnosis_history = relationship("DiagnosisHistory", back_populates="scan")


class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    scans_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="diagnosis_history")
    scan = relationship("Scans", back_populates="diagnosis_history")
    disease = relationship("Disease", back_populates="diagnosis_history")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)  # Symptoms as text field
    treatment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    image_url = Column(String(255), nullable=True)

    # Relationships
    scans = relationship("Scans", back_populates="disease")
    diagnosis_history = relationship("DiagnosisHistory", back_populates="disease")
    # Many-to-Many with Medicines through MedicineDiseaseLink
    medicine_links = relationship("MedicineDiseaseLink", back_populates="disease", cascade="all, delete-orphan")
    medicines = relationship("Medicines", secondary="medicine_disease_link", back_populates="diseases", viewonly=True)


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    logo_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    medicines = relationship("Medicines", back_populates="brand")
class Medicines(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    generic_name = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True)
    dosage = Column(String(100), nullable=True)
    side_effects = Column(Text, nullable=True)
    suitable_for = Column(String(10), nullable=True)
    price = Column(Float, nullable=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    image_url = Column(Text, nullable=True)  # JSON array of image URLs
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    brand = relationship("Brand", back_populates="medicines")
    disease_links = relationship("MedicineDiseaseLink", back_populates="medicine", cascade="all, delete-orphan")
    diseases = relationship("Disease", secondary="medicine_disease_link", back_populates="medicines", viewonly=True)
    medicine_pharmacies = relationship("MedicinePharmacyLink", back_populates="medicine")


# Medicine-Disease Link (Many-to-Many relationship)
class MedicineDiseaseLink(Base):
    __tablename__ = "medicine_disease_link"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    medicine = relationship("Medicines", back_populates="disease_links")
    disease = relationship("Disease", back_populates="medicine_links")

    # Unique constraint to prevent duplicate links
    __table_args__ = (
        UniqueConstraint('medicine_id', 'disease_id', name='unique_medicine_disease'),
    )


class Pharmacies(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    # Replaced open_hours (string) with structured open_time/close_time and is_open_247
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    is_open_247 = Column(Boolean, nullable=False, default=False)
    ratings = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_url = Column(Text, nullable=True)  # Store JSON array of image URLs
    logo_url = Column(String(255), nullable=True)  # Pharmacy logo

    # Relationships
    medicine_pharmacies = relationship("MedicinePharmacyLink", back_populates="pharmacy")


class MedicinePharmacyLink(Base):
    __tablename__ = "medicine_pharmacy_link"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    stock = Column(String(50), nullable=True)
    price = Column(Float, nullable=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    medicine = relationship("Medicines", back_populates="medicine_pharmacies")
    pharmacy = relationship("Pharmacies", back_populates="medicine_pharmacies")


class ChatSessions(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessages", back_populates="chat_session")


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # e.g., 'user' or 'assistant' or 'system'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True) # To store the list of products or pharmacies metadata (RAG sources)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chat_session = relationship("ChatSessions", back_populates="chat_messages")


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
