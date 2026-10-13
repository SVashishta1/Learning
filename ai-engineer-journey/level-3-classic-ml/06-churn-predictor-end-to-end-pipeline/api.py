"""Project 3.6 step 2: serve the saved model behind an API (Level 1 skills + Level 3 model)."""
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = Path(__file__).with_name("churn_model.joblib")
app = FastAPI(title="Churn predictor")
bundle = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None


class Customer(BaseModel):
    contract: Literal["month-to-month", "one-year", "two-year"]
    tenure_months: int = Field(ge=0, le=120)
    monthly_charges: float = Field(gt=0, le=500)
    support_calls: int = Field(ge=0, le=50)
    internet: Literal["fiber", "dsl", "none"]
    payment_method: Literal["card", "bank", "electronic-check"]


@app.post("/predict")
def predict(customer: Customer):
    if bundle is None:
        raise HTTPException(503, "Model not trained yet. Run: python train.py")
    row = pd.DataFrame([customer.model_dump()])[bundle["features"]]
    p = float(bundle["pipeline"].predict_proba(row)[0, 1])
    action = "call them with a retention offer" if p > 0.5 else "no action needed"
    return {"churn_probability": round(p, 3), "risk": "high" if p > 0.5 else "low", "suggested_action": action,
            "model": bundle["model_name"]}
