from pydantic import BaseModel
from typing import Optional, List

class UserRegister(BaseModel):
    name: str
    contact: str
    password: str
    role: str
    location: Optional[str] = "Central Region, UP"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    kyc_document: Optional[str] = None

class UserLogin(BaseModel):
    contact: str
    password: str

# Retained for backwards compatibility
class UserAuth(BaseModel):
    name: Optional[str] = None
    contact: str
    password: str
    role: Optional[str] = "farmer"
    location: Optional[str] = "Central Region, UP"

class CropCreate(BaseModel):
    crop_name: str
    variety: Optional[str] = "Desi"
    quantity_kg: float
    expected_price: float
    grade: Optional[str] = "A"
    packaging: Optional[str] = "Plastic Crates"
    location: Optional[str] = "Central Region, UP"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ExpenseCreate(BaseModel):
    seeds: float
    fertilizer: float
    labour: float
    transport: float
    misc: float
    expected_revenue: float

class AiGradingRequest(BaseModel):
    crop_name: str
    image_base64: Optional[str] = None

class AiPricingRequest(BaseModel):
    crop_name: str
    variety: Optional[str] = "Standard"
    location: Optional[str] = "Central Region"
    grade: Optional[str] = "Grade A"
    quantity_kg: Optional[float] = 100.0

class KycVerifyRequest(BaseModel):
    user_id: int
    status: str  # VERIFIED or REJECTED