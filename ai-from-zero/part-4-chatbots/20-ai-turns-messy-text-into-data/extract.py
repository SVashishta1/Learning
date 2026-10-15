# Turn messy text (receipts, emails, notes) into clean, structured data you can put in a spreadsheet.
import csv

from pydantic import BaseModel

import ai


# The "form" we want the AI to fill in. Each line is a box on the form.
class Receipt(BaseModel):
    shop: str
    date: str | None            # "str | None" means: text, or empty if it isn't in the document
    total: float
    currency: str
    items: list[str]


messy_texts = [
    "CAFE LUNA Milano 14/10/2026  2x cappuccino 3,60  cornetto 1,50  TOTALE EUR 5,10",
    "hey! paid joe's plumbing $142 on sept 30 for fixing the kitchen tap + a new hose",
    "Amazon order confirmation. Oct 2, 2026. USB-C cable $9.99, Desk lamp $24.50. Order total: $34.49",
]

rows = []
for text in messy_texts:
    receipt = ai.ask_for_data(f"Fill in the receipt form from this text:\n{text}", Receipt)
    print(f"✅ {receipt.shop:20s} {receipt.date or '?':12s} {receipt.total:8.2f} {receipt.currency}  items: {receipt.items}")
    rows.append({**receipt.model_dump(), "items": ", ".join(receipt.items)})

# Save everything to a CSV file that Excel or Google Sheets can open ("utf-8-sig" keeps € and accents readable in Excel)
with open("receipts.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(Receipt.model_fields))   # the columns = the boxes on the form
    writer.writeheader()
    writer.writerows(rows)
print("\nSaved receipts.csv. Open it in Excel or Google Sheets!")
