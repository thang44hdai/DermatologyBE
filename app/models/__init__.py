"""
Export all models - Database models and AI model
"""

from .ai_model import SkinDiseaseFusionModel

# Core
from app.db.session import Base

# Authentication & Users
from .user import (
    User,
    UserRole,
    AppLogs,
    Notifications,
)

# AI Diagnosis & Scans
from .medical import (
    Scans,
    DiagnosisHistory,
    Disease,
)

# Medicine & Pharmacies
from .product import (
    Medicines,
    Brand,
    Category,
    Pharmacies,
    MedicineDiseaseLink,
    MedicinePharmacyLink,
)

# Chat
from .chat import (
    ChatSessions,
    ChatMessages,
)

# System
from .reminder import (
    MedicationReminder,
    AdherenceLog,
)

__all__ = [
    # AI Model
    "SkinDiseaseFusionModel",
    
    # Core
    "Base",
    "UserRole",
    
    # Authentication & Users
    "User",
    "AppLogs",
    "Notifications",
    
    # AI Diagnosis & Scans
    "Scans",
    "DiagnosisHistory",
    "Disease",
    
    # Medicine & Pharmacies
    "Medicines",
    "Brand",
    "Category",
    "Pharmacies",
    "MedicineDiseaseLink",
    "MedicinePharmacyLink",
    
    # Chat
    "ChatSessions",
    "ChatMessages",
    
    # System
    "MedicationReminder",
    "AdherenceLog",
]
