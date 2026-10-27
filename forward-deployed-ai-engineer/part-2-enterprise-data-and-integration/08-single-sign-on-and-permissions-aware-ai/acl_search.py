# acl_search.py: search that only ever sees documents the user is allowed to see.
#
# ACL = "access control list": for each document, the groups allowed to read it.
# The golden rule: FILTER FIRST, THEN RANK. Restricted documents must never reach the ranking step,
# the LLM prompt, the citations, the logs or the result count.
import re

DOCUMENTS = [
    {"id": "DOC-1", "title": "Delivery terms", "allowed_groups": ["staff"],
     "text": "If a shipment is delayed, inform the customer of the new delivery time. For delays over 24 hours "
             "caused by Northwind, business customers may request a 10% credit on the transport charge."},
    {"id": "DOC-2", "title": "WISMO reply macros", "allowed_groups": ["support"],
     "text": "Where is my shipment replies: give the last scan, the new delivery time and an apology. "
             "Never promise a credit; point to the delivery terms instead."},
    {"id": "DOC-3", "title": "Credit note approval limits", "allowed_groups": ["finance", "management"],
     "text": "Credit notes up to 1,000 EUR are approved by finance. Above 1,000 EUR the CFO must approve. "
             "Brouwer Metals has a special payment plan: 60 days instead of 30."},
    {"id": "DOC-4", "title": "Claims handling procedure", "allowed_groups": ["claims", "management"],
     "text": "Damage claims need photos and the packing list. Claims above 5,000 EUR go to the insurer. "
             "Delayed shipment claims are only paid for perishable goods."},
    {"id": "DOC-5", "title": "Salary bands 2027", "allowed_groups": ["management"],
     "text": "Support agent salary band: 34,000 to 41,000 EUR. Team lead: 45,000 to 52,000 EUR. "
             "Raises for delayed reviews are paid back to January."},
]


def allowed(document, user_groups):
    """True if the user shares at least one group with the document's access list."""
    return bool(set(document["allowed_groups"]) & set(user_groups))


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def score(query, document):
    """A tiny keyword score: how many query words appear in the title or text (title words count double)."""
    title, body = set(words(document["title"])), set(words(document["text"]))
    return sum(2 if w in title else 1 if w in body else 0 for w in set(words(query)))


def search(query, user_groups, top_k=3, documents=DOCUMENTS):
    """1) keep only documents this user may read, 2) rank those, 3) return the best top_k with a score > 0."""
    visible = [d for d in documents if allowed(d, user_groups)]           # FILTER FIRST
    ranked = sorted(visible, key=lambda d: score(query, d), reverse=True)  # THEN RANK
    return [d for d in ranked if score(query, d) > 0][:top_k]
