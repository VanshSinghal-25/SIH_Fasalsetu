from pydantic import BaseModel
from typing import Optional

class UserAuth(BaseModel):
    name: str
    contact: str
    password: str
    role: str
    location: Optional[str] = "Central Region, UP"

class CropCreate(BaseModel):
    crop_name: str
    variety: str
    quantity_kg: float
    expected_price: float
    grade: str = "A"
    packaging: str

class ExpenseCreate(BaseModel):
    seeds: float
    fertilizer: float
    labour: float
    transport: float
    misc: float
    expected_revenue: float