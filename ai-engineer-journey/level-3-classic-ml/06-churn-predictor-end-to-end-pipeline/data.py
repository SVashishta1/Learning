"""Generates a realistic-looking telecom customer table with a 'churned' column (did they leave?)."""
import numpy as np
import pandas as pd


def make_customers(n=3000, seed=11):
    rng = np.random.default_rng(seed)
    contract = rng.choice(["month-to-month", "one-year", "two-year"], n, p=[0.55, 0.25, 0.20])
    tenure = rng.integers(1, 72, n)
    monthly = rng.normal(70, 25, n).clip(20, 130).round(2)
    support_calls = rng.poisson(1.5, n)
    internet = rng.choice(["fiber", "dsl", "none"], n, p=[0.45, 0.4, 0.15])
    payment = rng.choice(["card", "bank", "electronic-check"], n)
    # Hidden churn rule: month-to-month, short tenure, high bills and many support calls -> likely to leave
    logit = (-1.0 + 1.6 * (contract == "month-to-month") - 1.2 * (contract == "two-year") - 0.04 * tenure
             + 0.02 * (monthly - 70) + 0.45 * support_calls + 0.5 * (payment == "electronic-check") + 0.3 * (internet == "fiber"))
    churned = rng.random(n) < 1 / (1 + np.exp(-logit))
    df = pd.DataFrame({"contract": contract, "tenure_months": tenure, "monthly_charges": monthly,
                       "support_calls": support_calls, "internet": internet, "payment_method": payment,
                       "churned": churned.astype(int)})
    df.loc[rng.random(n) < 0.03, "monthly_charges"] = np.nan    # real data has holes
    return df
