# Step 2: load the saved model and offer predictions through an API (Part 1 + Part 2 together!).
# Run train.py first, then: uvicorn api:app --reload
from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_FILE = Path(__file__).parent / "house_model.joblib"     # the file train.py saved, in this same folder
if not MODEL_FILE.exists():
    raise SystemExit("No house_model.joblib yet. Run `python train.py` first, then start the server again.")

app = FastAPI()
model = joblib.load(MODEL_FILE)          # load ONCE when the server starts, not on every request


class House(BaseModel):
    size_m2: float = Field(gt=10, lt=2000)        # Field(...) rejects silly inputs like -5 m²
    bedrooms: int = Field(ge=0, le=20)
    km_to_centre: float = Field(ge=0, le=200)


@app.post("/predict")
def predict(house: House):
    price = model.predict([[house.size_m2, house.bedrooms, house.km_to_centre]])[0]
    return {"estimated_price": int(round(price, -3))}    # round to the nearest 1,000, as a whole number
