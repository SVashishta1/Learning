import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

HERE = Path(__file__).parent
# The API needs a trained model. Train one first if it doesn't exist yet (takes ~30 seconds).
if not (HERE / "churn_model.joblib").exists():
    subprocess.run([sys.executable, "train.py"], check=True, cwd=HERE)

from api import app  # noqa: E402

client = TestClient(app)
risky = {"contract": "month-to-month", "tenure_months": 2, "monthly_charges": 110, "support_calls": 6,
         "internet": "fiber", "payment_method": "electronic-check"}
loyal = {"contract": "two-year", "tenure_months": 60, "monthly_charges": 40, "support_calls": 0,
         "internet": "dsl", "payment_method": "bank"}


def test_risky_customer_scores_higher_than_loyal():
    r1, r2 = client.post("/predict", json=risky).json(), client.post("/predict", json=loyal).json()
    assert r1["churn_probability"] > 0.7 > 0.2 > r2["churn_probability"]


def test_invalid_input_rejected():
    assert client.post("/predict", json={**risky, "contract": "forever"}).status_code == 422


def test_missing_field_rejected():
    incomplete = {k: v for k, v in risky.items() if k != "tenure_months"}
    assert client.post("/predict", json=incomplete).status_code == 422
