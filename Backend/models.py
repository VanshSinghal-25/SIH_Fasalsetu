from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # farmer, wholesaler, consumer, driver
    location = Column(String, default="Central Region")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    kyc_status = Column(String, default="PENDING")  # PENDING, VERIFIED, REJECTED
    kyc_document = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Crop(Base):
    __tablename__ = "crops"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    crop_name = Column(String, nullable=False)
    variety = Column(String, nullable=True)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    grade = Column(String, default="Grade A")
    ai_quality_score = Column(Float, default=0.0)
    ai_freshness_index = Column(String, default="Standard")
    packaging = Column(String, nullable=True)
    status = Column(String, default="AVAILABLE")
    location = Column(String, default="Central Region")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CropExpense(Base):
    __tablename__ = "crop_expenses"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    crop_name = Column(String, default="Tomato")
    seeds = Column(Float, default=0.0)
    fertilizer = Column(Float, default=0.0)
    labour = Column(Float, default=0.0)
    transport = Column(Float, default=0.0)
    misc = Column(Float, default=0.0)
    expected_revenue = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    buyer_name = Column(String, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    stage = Column(String, default="Confirmed")
    escrow_status = Column(String, default="HELD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())