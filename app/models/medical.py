from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Scans(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scan_date = Column(DateTime, nullable=False)
    image_url = Column(String(255), nullable=False)
    highlighted_image_url = Column(String(500), nullable=True)  # URL of highlighted/annotated scan image
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
