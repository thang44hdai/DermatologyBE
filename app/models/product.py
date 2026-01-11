from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint, Time, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    logo_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    medicines = relationship("Medicines", back_populates="brand")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    medicines = relationship("Medicines", back_populates="category")

class Medicines(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    generic_name = Column(String(255), nullable=True)
    type = Column(String(100), nullable=True)
    dosage = Column(String(500), nullable=True)
    side_effects = Column(Text, nullable=True)
    suitable_for = Column(String(255), nullable=True)
    price = Column(Float, nullable=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image_url = Column(Text, nullable=True)  # JSON array of image URLs
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    brand = relationship("Brand", back_populates="medicines")
    category = relationship("Category", back_populates="medicines")
    disease_links = relationship("MedicineDiseaseLink", back_populates="medicine", cascade="all, delete-orphan")
    diseases = relationship("Disease", secondary="medicine_disease_link", back_populates="medicines", viewonly=True)
    medicine_pharmacies = relationship("MedicinePharmacyLink", back_populates="medicine")

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
