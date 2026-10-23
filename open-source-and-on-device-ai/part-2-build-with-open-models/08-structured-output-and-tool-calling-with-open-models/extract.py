"""Structured output: turn messy customer emails into clean, checked data with a LOCAL model.

Ollama's `format` option takes a JSON schema and forces the model to answer in exactly that shape.
Pydantic writes the schema for us and checks the answer.

Run:  python extract.py
"""
import os
import sys
from typing import Literal, Optional

import ollama
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("MODEL", "qwen2.5:3b")


# The shape we want. Every field has a type; Field(description=...) tells the model what to put there.
# (The class docstring below also goes into the schema, so it is written for the model.)
class SupportTicket(BaseModel):
    """A customer support ticket extracted from one email."""
    customer_name: str
    order_number: Optional[str] = Field(description="like RB-1234, or null if the email has none")
    product: str = Field(description="the product the email is about, in a few words")
    problem: str = Field(description="the problem in one short sentence")
    urgency: Literal["low", "medium", "high"]
    wants_refund: bool


EMAILS = [
    "Hi, it's Maria Lopez. The e-bike I bought last week (order RB-2207) won't charge any more. "
    "I need it to get to work on Monday!! Please fix it or give me my money back.",
    "hello, my kids helmet strap broke on the 1st day, not urgent but pls send a new one. thx, Tom Becker",
    "Good morning, this is Dr. Aisha Rahman. Order RB-1188: the brakes on my road bike squeal loudly. "
    "Could you take a look at some point? Kind regards.",
]


def extract(email):
    """Ask the model for a SupportTicket. If the answer does not fit the schema, try once more."""
    schema = SupportTicket.model_json_schema()  # a dict that describes the fields and their types
    messages = [
        {"role": "system", "content": "Extract a support ticket from the customer email. "
                                      f"Answer with JSON matching this schema: {schema}"},
        {"role": "user", "content": email},
    ]
    for attempt in range(2):
        response = ollama.chat(model=MODEL, messages=messages, format=schema, options={"temperature": 0})
        try:
            return SupportTicket.model_validate_json(response.message.content)  # check every field
        except ValidationError as e:
            print(f"  (attempt {attempt + 1} did not fit the schema: {e.error_count()} problem(s), retrying)")
    raise RuntimeError("The model could not produce a valid ticket.")


def main():
    try:
        for email in EMAILS:
            print("\nEMAIL:", email)
            ticket = extract(email)
            print("TICKET:", ticket.model_dump_json(indent=2))
            if ticket.urgency == "high":
                print(f"-> {ticket.customer_name} goes to the front of the queue.")  # real Python data now
    except ConnectionError:
        sys.exit("Can't reach Ollama. Open the Ollama app or run `ollama serve`.")
    except ollama.ResponseError as e:
        sys.exit(f"Ollama says: {e.error}  (try: ollama pull {MODEL})")


if __name__ == "__main__":
    main()
