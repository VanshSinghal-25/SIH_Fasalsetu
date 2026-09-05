from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models, schemas
from database import engine, get_db
from security import hash_password, verify_password, create_access_token

# Automatically generate tables in SQLite
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FasalSetu API Engine")

# Enable Cross-Origin Resource Sharing so browser HTML can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/login")
def login(user_data: schemas.UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.contact == user_data.contact).first()
    
    if not user:
        user = models.User(
            name=user_data.name,
            contact=user_data.contact,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            location=user_data.location or "Central Region"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect contact or password."
            )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    
    return {
        "status": "success",
        "token": token,
        "user_id": user.id,
        "name": user.name,
        "role": user.role,
        "location": user.location
    }

@app.get("/api/crops")
def get_crops(db: Session = Depends(get_db)):
    return db.query(models.Crop).filter(models.Crop.status == "AVAILABLE").all()

@app.post("/api/crops")
def add_crop(crop_in: schemas.CropCreate, db: Session = Depends(get_db)):
    new_crop = models.Crop(
        farmer_id=1,
        crop_name=crop_in.crop_name,
        variety=crop_in.variety,
        quantity_kg=crop_in.quantity_kg,
        price_per_kg=crop_in.expected_price,
        grade=crop_in.grade,
        packaging=crop_in.packaging
    )
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return {"message": "Crop posted to marketplace", "crop": new_crop}

@app.post("/api/expenses/calculate")
def calculate_and_save_expense(exp: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    total_cost = exp.seeds + exp.fertilizer + exp.labour + exp.transport + exp.misc
    net_profit = exp.expected_revenue - total_cost
    margin_pct = round((net_profit / exp.expected_revenue * 100), 1) if exp.expected_revenue > 0 else 0.0

    record = models.CropExpense(
        farmer_id=1,
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