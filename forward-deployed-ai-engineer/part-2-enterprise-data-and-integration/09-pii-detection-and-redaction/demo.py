# demo.py: the full privacy round trip on a real-looking customer email.
#
#   python demo.py              find PII -> mask for logs -> pseudonymise -> LLM drafts a reply -> restore
#   python demo.py --ner        also use spaCy's NER model to find names nobody listed
#
# The LLM only ever sees placeholders like <PERSON_1>. Real values stay on your machine.
import argparse

import llm
import pii
from safe_logging import get_logger

EMAIL = """Hello,

My pallet NW-4821907 to Utrecht is late again (promised 2026-10-20). Please refund the 10% credit to
NL91 ABNA 0417 1643 00, or charge my card 4111 1111 1111 1111 for the re-delivery.
Call me on +31 6 1234 5678 or my office 030 555 0199. Ms Kowalska from your team said it was fixed,
but your driver Pieter Bakker never came.
Our portal logs show the order came from 192.168.10.24. Invoice INV-2291, amount 1,250.00 EUR.

Regards,
Joost van Dijk
joost.vandijk@brouwer-metals.example
"""
KNOWN_NAMES = ["Joost van Dijk", "Joost"]      # in real life: contact names from the CRM for this sender
SYSTEM = ("You draft short, polite replies for Northwind Customer Support. The email contains placeholders like "
          "<PERSON_1> or <IBAN_1>. Keep every placeholder exactly as written; never invent new ones or real values.")
EXAMPLE_REPLY = ("Dear {customer},\n\nI'm sorry your pallet NW-4821907 is late again. I've asked our finance team "
                 "to process the 10% credit to your account {iban}; we won't charge your card. "
                 "We'll call you on {phone} as soon as we have the new delivery time.\n\n"
                 "Kind regards,\nNorthwind Customer Support")


def main():
    parser = argparse.ArgumentParser(description="Privacy round trip on a customer email.")
    parser.add_argument("--ner", action="store_true", help="also detect names with spaCy (optional install)")
    args = parser.parse_args()
    log = get_logger()

    print("1) PII found:")
    for f in pii.find_pii(EMAIL, KNOWN_NAMES, use_ner=args.ner):
        print(f"   {f.kind:<12} {f.text!r:<42} via {f.source}")

    print("\n2) What a careless log line would write, after the safety-net filter:")
    log.info("new ticket body: %s", EMAIL.splitlines()[3])

    shield = pii.Pseudonymiser(KNOWN_NAMES, use_ner=args.ner)
    safe_email = shield.pseudonymise(EMAIL)
    print("\n3) What the LLM receives:\n" + safe_email)

    try:
        reply = llm.ask(f"Draft a reply to this customer email:\n<email>\n{safe_email}</email>", system=SYSTEM)
        print(f"4) LLM reply ({llm.PROVIDER}, {llm.model_name()}), still with placeholders:\n{reply}\n")
    except (Exception, SystemExit) as problem:
        reply = EXAMPLE_REPLY.format(customer=shield.placeholder_for("PERSON", "Joost van Dijk"),   # what the
                                     iban=shield.placeholder_for("IBAN", "NL91 ABNA 0417 1643 00"),  # model would
                                     phone=shield.placeholder_for("PHONE", "+31 6 1234 5678"))       # write back
        print(f"4) No AI available ({str(problem).split('. ')[0]}).\n"
              f"   Using an EXAMPLE reply of the kind the LLM writes:\n{reply}\n")

    print("5) Restored on our side, ready for the agent to review:\n" + shield.restore(reply))
    log.info("drafted reply for ticket %s using %d placeholders", "T-1042", len(shield.vault))


if __name__ == "__main__":
    main()
