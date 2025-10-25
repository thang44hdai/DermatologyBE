"""
Export all models - Database models and AI model
"""

from .ai_model import SkinDiseaseFusionModel
from .database import (
    # Core
    Base,
    UserRole,
    
    # Authentication & Users
    User,
    
    # AI Diagnosis & Scans
    Scans,
    DiagnosisHistory,
    Disease,
    Symptoms,
    
    # Medicine & Pharmacies
    Medicines,
    Pharmacies,
    MedicinePharmacyLink,
    
    # Chat
    ChatSessions,
    ChatMessages,
    
    # Quiz System
    QuizCategories,
    Quizzes,
    Questions,
    Answers,
    UserAnswers,
    QuizAttempts,
    
    # System
    AppLogs,
    Notifications,
)

__all__ = [
    # AI Model
    "SkinDiseaseFusionModel",
    
    # Core
    "Base",
    "UserRole",
    
    # Authentication & Users
    "User",
    
    # AI Diagnosis & Scans
    "Scans",
    "DiagnosisHistory",
    "Disease",
    "Symptoms",
    
    # Medicine & Pharmacies
    "Medicines",
    "Pharmacies",
    "MedicinePharmacyLink",
    
    # Chat
    "ChatSessions",
    "ChatMessages",
    
    # Quiz System
    "QuizCategories",
    "Quizzes",
    "Questions",
    "Answers",
    "UserAnswers",
    "QuizAttempts",
    
    # System
    "AppLogs",
    "Notifications",
]
