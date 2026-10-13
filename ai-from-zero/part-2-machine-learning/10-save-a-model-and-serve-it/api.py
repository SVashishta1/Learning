# Step 2: load the saved model and offer predictions through an API (Part 1 + Part 2 together!).
import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()
model = joblib.load("house_model.joblib")          # load ONCE when the server starts


class House(BaseModel):
    size_m2: float = Field(gt=10, lt=2000)        # Field(...) rejects silly inputs like -5 m²
    bedrooms: int = Field(ge=0, le=20)
    km_to_centre: float = Field(ge=0, le=200)


@app.post("/predict")
def predict(house: House):
    price = model.predict([[house.size_m2, house.bedrooms, house.km_to_centre]])[0]
    return {"estimated_price": round(price, -3)}
