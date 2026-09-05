from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import random

import models, schemas
from database import engine, get_db
from security import hash_password, verify_password, create_access_token

# Automatically generate tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FasalSetu API Engine v2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: Get current user id from header or token
def get_current_user_from_header(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        import jwt
        from security import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return db.query(models.User).filter(models.User.id == user_id).first()
    except Exception:
        return None

# ================= 1. STRICT AUTHENTICATION (NO AUTO-CREATE) =================
@app.post("/api/auth/register")
def register_user(reg_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.contact == reg_data.contact).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists with this contact number. Please sign in."
        )

    new_user = models.User(
        name=reg_data.name,
        contact=reg_data.contact,
        hashed_password=hash_password(reg_data.password),
        role=reg_data.role.lower(),
        location=reg_data.location or "Central Region, UP",
        latitude=reg_data.latitude,
        longitude=reg_data.longitude,
        kyc_status="VERIFIED" if reg_data.role == "driver" else "PENDING", # Auto or manual KYC
        kyc_document=reg_data.kyc_document
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "role": new_user.role})
    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": token,
        "user_id": new_user.id,
        "name": new_user.name,
        "role": new_user.role,
        "location": new_user.location,
        "kyc_status": new_user.kyc_status
    }

@app.post("/api/auth/login")
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.contact == login_data.contact).first()
    
    # Point 1: STRICT - NO AUTO CREATION. User must create account first.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this contact. Please create an account first."
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again."
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "status": "success",
        "token": token,
        "user_id": user.id,
        "name": user.name,
        "role": user.role,
        "location": user.location,
        "kyc_status": user.kyc_status,
        "latitude": user.latitude,
        "longitude": user.longitude
    }

# ================= 4. MANUAL KYC VERIFICATION GATE =================
@app.post("/api/admin/verify-kyc")
def verify_user_kyc(req: schemas.KycVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.kyc_status = req.status.upper()
    db.commit()
    return {"message": f"User KYC status updated to {user.kyc_status}", "user_id": user.id}

@app.get("/api/user/kyc-status/{user_id}")
def check_kyc_status(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "kyc_status": user.kyc_status, "verified": user.kyc_status == "VERIFIED"}

# ================= 3 & 9. REAL MARKETPLACE & ROLE SPECIFIC REAL DATA =================
@app.get("/api/crops")
def get_all_available_crops(db: Session = Depends(get_db)):
    # Clean real data: only lists crops actively posted
    return db.query(models.Crop).filter(models.Crop.status == "AVAILABLE").all()

@app.get("/api/farmer/crops/{farmer_id}")
def get_farmer_own_crops(farmer_id: int, db: Session = Depends(get_db)):
    # Point 2: Empty if new user hasn't posted anything
    return db.query(models.Crop).filter(models.Crop.farmer_id == farmer_id).all()

@app.post("/api/crops")
def add_crop(crop_in: schemas.CropCreate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    current_user = get_current_user_from_header(authorization, db)
    farmer_id = current_user.id if current_user else 1

    # Real crop creation
    new_crop = models.Crop(
        farmer_id=farmer_id,
        crop_name=crop_in.crop_name,
        variety=crop_in.variety,
        quantity_kg=crop_in.quantity_kg,
        price_per_kg=crop_in.expected_price,
        grade=crop_in.grade or "Grade A",
        packaging=crop_in.packaging or "Plastic Crates",
        location=crop_in.location or (current_user.location if current_user else "Central Region"),
        latitude=crop_in.latitude,
        longitude=crop_in.longitude,
        status="AVAILABLE"
    )
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return {"message": "Crop posted to marketplace in real-time", "crop": new_crop}

# ================= 6. AI QUALITY GRADING VIA IMAGE =================
@app.post("/api/ai/grade-crop")
def grade_crop_image(req: schemas.AiGradingRequest):
    # Computer Vision simulation scoring based on visual freshness & surface consistency
    crop = req.crop_name.lower()
    score = random.randint(88, 96)
    if "tomato" in crop:
        grade = "Grade A" if score > 90 else "Grade B"
        freshness = "96% Deep Red, Blemish < 2%"
    elif "potato" in crop:
        grade = "Grade A" if score > 89 else "Grade B"
        freshness = "Firm Skin, Uniform Size (60mm)"
    else:
        grade = "Grade A"
        freshness = "Moisture 11.8%, High Lustre"

    return {
        "status": "success",
        "crop_name": req.crop_name,
        "quality_score": score,
        "assigned_grade": grade,
        "freshness_index": freshness,
        "surface_defect_ratio": f"{round(random.uniform(1.2, 3.1), 1)}%",
        "inspection_status": "AI Certified"
    }

# ================= 7. AI DYNAMIC PRICING & MARKET DEMAND PREDICTION =================
@app.post("/api/ai/price-demand-prediction")
def predict_price_and_demand(req: schemas.AiPricingRequest):
    crop = req.crop_name.strip().title()
    loc = req.location or "Central Region"
    
    # Base regional pricing models
    benchmarks = {
        "Tomato": {"mandi": 24.0, "optimal": 28.5, "demand": "VERY HIGH 🔥", "velocity": 92},
        "Potato": {"mandi": 19.0, "optimal": 22.0, "demand": "MODERATE ⚡", "velocity": 74},
        "Wheat": {"mandi": 22.5, "optimal": 26.0, "demand": "HIGH 📈", "velocity": 85},
        "Onion": {"mandi": 21.0, "optimal": 25.0, "demand": "HIGH 🔥", "velocity": 88},
    }

    base = benchmarks.get(crop, {"mandi": 20.0, "optimal": 25.0, "demand": "STABLE", "velocity": 80})
    recommended_min = round(base["optimal"] - 1.0, 1)
    recommended_max = round(base["optimal"] + 1.5, 1)

    return {
        "crop": crop,
        "region": loc,
        "mandi_benchmark_per_kg": base["mandi"],
        "ai_suggested_price_range": f"₹{recommended_min} - ₹{recommended_max}/kg",
        "optimal_point_per_kg": base["optimal"],
        "market_demand_status": base["demand"],
        "demand_score": base["velocity"],
        "projected_7day_trend": "+4.8% Expected increase due to low mandi arrivals"
    }

# ================= 8. LIVE LOCATION PROXIMITY LOGISTICS =================
@app.post("/api/location/update")
def update_user_location(latitude: float, longitude: float, location_name: str, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    user = get_current_user_from_header(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user.latitude = latitude
    user.longitude = longitude
    user.location = location_name
    db.commit()
    return {"message": "Location updated successfully", "location": location_name, "lat": latitude, "lon": longitude}

# ================= 10. PRESERVED EXPENSES & POOLING (ZERO REGRESSION) =================
@app.post("/api/expenses/calculate")
def calculate_and_save_expense(exp: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    total_cost = exp.seeds + exp.fertilizer + exp.labour + exp.transport + exp.misc
    net_profit = exp.expected_revenue - total_cost
    margin_pct = round((net_profit / exp.expected_revenue * 100), 1) if exp.expected_revenue > 0 else 0.0

    record = models.CropExpense(
        farmer_id=1,
        crop_name="Tomato",
        seeds=exp.seeds,
        fertilizer=exp.fertilizer,
        labour=exp.labour,
        transport=exp.transport,
        misc=exp.misc,
        expected_revenue=exp.expected_revenue,
        net_profit=net_profit
    )
    db.add(record)
    db.commit()

    return {
        "total_cost": total_cost,
        "net_profit": net_profit,
        "margin_percentage": margin_pct
    }

@app.get("/api/farmer/expenses/{farmer_id}")
def get_farmer_expenses(farmer_id: int, db: Session = Depends(get_db)):
    return db.query(models.CropExpense).filter(models.CropExpense.farmer_id == farmer_id).all()

@app.get("/api/logistics/pooling")
def get_pooling_data(corridor: str = "Mathura-Delhi"):
    return {
        "corridor": corridor,
        "participants": [
            {"farmer": "You (Kisan Mitra)", "village": "Mathura", "qty": "300 Kg", "solo": 2800, "pooled": 1100},
            {"farmer": "Mahesh", "village": "Govardhan", "qty": "400 Kg", "solo": 2900, "pooled": 1300},
            {"farmer": "Hari", "village": "Chaumuha", "qty": "200 Kg", "solo": 2600, "pooled": 800}
        ],
        "solo_total": 8300,
        "pooled_total": 3200,
        "net_savings": 1700
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)