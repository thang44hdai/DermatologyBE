from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scans = relationship("Scans", back_populates="user")
    diagnosis_history = relationship("DiagnosisHistory", back_populates="user")
    notifications = relationship("Notifications", back_populates="user")
    app_logs = relationship("AppLogs", back_populates="user")
    user_answers = relationship("UserAnswers", back_populates="user")
    quiz_attempts = relationship("QuizAttempts", back_populates="user")
    chat_sessions = relationship("ChatSessions", back_populates="user")


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
    image_url = Column(Text, nullable=True)  # JSON array of image URLs
    created_at = Column(DateTime, server_default=func.now())

    # Relationships - Many-to-Many with Disease through MedicineDiseaseLink
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
    open_hours = Column(String(100), nullable=True)
    ratings = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

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

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessages", back_populates="chat_session")


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(String(50), nullable=False)  # e.g., 'user' or 'bot'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    # Relationships
    chat_session = relationship("ChatSessions", back_populates="chat_messages")


class QuizCategories(Base):
    __tablename__ = "quiz_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    quizzes = relationship("Quizzes", back_populates="quiz_category")


class Quizzes(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey("quiz_categories.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    quiz_category = relationship("QuizCategories", back_populates="quizzes")
    questions = relationship("Questions", back_populates="quiz")
    quiz_attempts = relationship("QuizAttempts", back_populates="quiz")


class Questions(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    content = Column(Text, nullable=False)
    point = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quizzes", back_populates="questions")
    answers = relationship("Answers", back_populates="question")
    user_answers = relationship("UserAnswers", back_populates="question")


class Answers(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_correct = Column(Integer, nullable=False)

    # Relationships
    question = relationship("Questions", back_populates="answers")


class UserAnswers(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Integer, nullable=False)
    answered_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_answers")
    question = relationship("Questions", back_populates="user_answers")


class QuizAttempts(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quizzes", back_populates="quiz_attempts")


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
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    type = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
