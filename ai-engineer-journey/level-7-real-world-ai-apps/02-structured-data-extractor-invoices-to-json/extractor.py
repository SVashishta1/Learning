"""Project 7.2: turn messy invoices/receipts/emails into clean, VALIDATED JSON.

python extractor.py samples/*.txt          # prints JSON for each file + writes extracted.csv
python extractor.py my_invoice.pdf         # PDFs work too (sent to Claude as a document)
"""
import base64
import csv
import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field

import llm


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float


class Invoice(BaseModel):
    vendor: str = Field(description="Business that issued the document")
    invoice_number: str | None = Field(description="Invoice/receipt number if present")
    date: str | None = Field(description="Issue date in ISO format YYYY-MM-DD")
    currency: str = Field(description="ISO 4217 code, e.g. USD, EUR")
    line_items: list[LineItem]
    subtotal: float | None
    tax: float | None = Field(description="Tax amount, 0 if explicitly none, null if unknown")
    total: float
    notes: str | None = Field(description="Anything important that doesn't fit elsewhere (due date, payment info)")


SYSTEM = ("You extract data from financial documents. Copy numbers exactly as written; "
          "never invent values. If a field is missing, use null. Convert dates to YYYY-MM-DD.")


def document_content(path: Path) -> list:
    if path.suffix.lower() == ".pdf":
        data = base64.standard_b64encode(path.read_bytes()).decode()
        return [{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
                {"type": "text", "text": "Extract the invoice data from this PDF."}]
    return [{"type": "text", "text": f"Extract the invoice data from this document:\n\n<document>\n{path.read_text()}\n</document>"}]


def check_math(inv: Invoice) -> list[str]:
    """LLMs can misread numbers. ALWAYS validate business rules in code afterwards."""
    problems = []
    for item in inv.line_items:
        if abs(item.quantity * item.unit_price - item.total) > 0.011:
            problems.append(f"line '{item.description}': {item.quantity} x {item.unit_price} != {item.total}")
    items_sum = round(sum(i.total for i in inv.line_items), 2)
    if inv.subtotal is not None and abs(items_sum - inv.subtotal) > 0.011:
        problems.append(f"line items sum to {items_sum} but subtotal says {inv.subtotal}")
    # Some receipts quote tax as already INCLUDED in the total (common in Europe), so accept either form.
    base = inv.subtotal if inv.subtotal is not None else items_sum
    if abs(base + (inv.tax or 0) - inv.total) > 0.011 and abs(base - inv.total) > 0.011:
        problems.append(f"subtotal {base} + tax {inv.tax} doesn't match total {inv.total}")
    return problems


def extract(client, path: Path) -> tuple[Invoice, list[str]]:
    response = llm.parse(client, max_tokens=4000, system=SYSTEM, output_format=Invoice,
                         messages=[{"role": "user", "content": document_content(path)}])
    invoice = response.parsed_output        # already a validated Invoice object, not a string!
    return invoice, check_math(invoice)


if __name__ == "__main__":
    client = llm.get_client()
    rows = []
    for name in sys.argv[1:] or sorted(str(p) for p in Path("samples").glob("*.txt")):
        inv, problems = extract(client, Path(name))
        print(f"\n=== {name} ===\n{inv.model_dump_json(indent=2)}")
        print("✅ numbers add up" if not problems else "⚠️  needs human review: " + "; ".join(problems))
        rows.append({"file": name, "vendor": inv.vendor, "date": inv.date, "currency": inv.currency,
                     "total": inv.total, "needs_review": bool(problems)})
    with open("extracted.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print("\nWrote extracted.csv. Open it in Excel or Google Sheets.")
