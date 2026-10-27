# pii.py: find personal data (PII) in text, then mask it, or swap it for placeholders you can swap back later.
#
# PII = "personally identifiable information": anything that identifies a person (name, email, phone,
# bank account, card number, IP address...). Three layers of detection, from most to least certain:
#   1. patterns + checksums   emails, phones, IBANs (mod-97 check), card numbers (Luhn check), IP addresses
#   2. lists you already have names of contacts from the CRM ("known names"), greeting and sign-off lines
#   3. NER (optional)         a small language model that spots person names it has never seen (spaCy)
import re
from dataclasses import dataclass

from cryptography.fernet import Fernet


@dataclass(frozen=True)
class Finding:
    start: int          # position of the first character in the text
    end: int            # position just after the last character
    kind: str           # EMAIL, PHONE, IBAN, CREDIT_CARD, IP_ADDRESS, PERSON
    text: str
    source: str         # "pattern", "list", "rule" or "ner"


# ---------- 1. patterns, with checksums where they exist ----------

PATTERNS = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b"),
    "CREDIT_CARD": re.compile(r"(?<![\d-])\d(?:[ -]?\d){12,18}(?![\d-])"),
    # International (+31 6 1234 5678, 0048 12 345 67 89) or national starting with 0 (06-12345678, 030 555 0199)
    "PHONE": re.compile(r"(?<![\w+])(?:(?:\+|00)\d{1,3}[ -]?(?:\(0\)[ -]?)?|0)\d{1,4}(?:[ -]?\d{2,4}){1,4}(?!\w)"),
    "IP_ADDRESS": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
}


def luhn_ok(number):
    """The Luhn checksum every payment card number passes; random digit strings usually fail it."""
    digits = [int(d) for d in re.sub(r"\D", "", number)][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


def iban_ok(iban):
    """The ISO 13616 mod-97 check: move the first 4 characters to the end, turn letters into numbers (A=10...)."""
    compact = iban.replace(" ", "")
    rearranged = compact[4:] + compact[:4]
    as_number = "".join(str(int(ch, 36)) for ch in rearranged)        # int('A', 36) == 10
    return 15 <= len(compact) <= 34 and int(as_number) % 97 == 1


def phone_ok(number):
    return 9 <= len(re.sub(r"\D", "", number)) <= 15               # real phone numbers have 9 to 15 digits


VALIDATORS = {"IBAN": iban_ok, "CREDIT_CARD": luhn_ok, "PHONE": phone_ok}


def find_patterns(text):
    found = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            check = VALIDATORS.get(kind)
            if check is None or check(match.group()):
                found.append(Finding(match.start(), match.end(), kind, match.group(), "pattern"))
    return found


# ---------- 2. names from lists and simple rules ----------

NAME = r"[A-Z][a-zà-ÿ]+(?:[ -](?:van|de|der|den|von|la|le)?\s?[A-Z][a-zà-ÿ]+)?"
NAME_RULES = [
    re.compile(rf"\b(?:Mr|Mrs|Ms|Dr)\.? ({NAME})"),                          # titles
    re.compile(rf"\b(?:[Mm]y name is|I am|I'm) ({NAME})"),                   # introductions
    re.compile(rf"^(?:Hi|Hello|Dear|Hey) ({NAME})\b", re.MULTILINE),          # greetings
    re.compile(rf"^(?:Regards|Best|Thanks|Cheers|Kind regards|Best regards),?\s*\n\s*({NAME})\s*$",
               re.MULTILINE),                                                  # sign-offs
]


def find_names(text, known_names=()):
    found = []
    for name in known_names:                                    # names you already know, e.g. from the CRM
        for match in re.finditer(rf"\b{re.escape(name)}\b", text, flags=re.IGNORECASE):
            found.append(Finding(match.start(), match.end(), "PERSON", match.group(), "list"))
    for rule in NAME_RULES:
        for match in rule.finditer(text):
            found.append(Finding(match.start(1), match.end(1), "PERSON", match.group(1), "rule"))
    return found


# ---------- 3. NER (optional): spaCy's small English model ----------

_nlp = None


def find_with_ner(text, model="en_core_web_sm"):
    """Person names a model recognises. Needs: pip install spacy, and the model (see the README)."""
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load(model)
    return [Finding(e.start_char, e.end_char, "PERSON", e.text, "ner") for e in _nlp(text).ents if e.label_ == "PERSON"]


# ---------- putting it together ----------

PRIORITY = {"pattern": 0, "list": 1, "rule": 2, "ner": 3}       # trust checked patterns most


def find_pii(text, known_names=(), use_ner=False):
    """All findings, without overlaps: when two overlap, keep the more trusted source (then the longer one)."""
    candidates = find_patterns(text) + find_names(text, known_names)
    if use_ner:
        candidates += find_with_ner(text)
    candidates.sort(key=lambda f: (PRIORITY[f.source], -(f.end - f.start)))
    kept = []
    for finding in candidates:
        if all(finding.end <= k.start or finding.start >= k.end for k in kept):
            kept.append(finding)
    return sorted(kept, key=lambda f: f.start)


def replace_findings(text, findings, replacement):
    """Replace each finding (from the end backwards, so earlier positions stay valid)."""
    for f in sorted(findings, key=lambda f: f.start, reverse=True):
        text = text[:f.start] + replacement(f) + text[f.end:]
    return text


def mask(text, known_names=(), use_ner=False):
    """One-way redaction: 'Call +31 6 1234 5678' -> 'Call [PHONE]'. Use it for logs and analytics."""
    return replace_findings(text, find_pii(text, known_names, use_ner), lambda f: f"[{f.kind}]")


class Pseudonymiser:
    """Reversible: every distinct value gets a stable placeholder like <PERSON_1>, kept in a private 'vault'.
    Send the placeholders to the LLM; put the real values back into its answer on your side."""

    def __init__(self, known_names=(), use_ner=False):
        self.known_names, self.use_ner = list(known_names), use_ner
        self.vault = {}            # placeholder -> real value  (sensitive! never log it, never send it)
        self._lookup = {}          # (kind, normalised value) -> placeholder

    def _placeholder(self, finding):
        key = (finding.kind, re.sub(r"\s", "", finding.text).lower())     # 'NL91 ABNA...' == 'NL91ABNA...'
        if key not in self._lookup:
            number = sum(1 for k, _ in self._lookup if k == finding.kind) + 1
            placeholder = f"<{finding.kind}_{number}>"
            self._lookup[key], self.vault[placeholder] = placeholder, finding.text
        return self._lookup[key]

    def pseudonymise(self, text):
        findings = find_pii(text, self.known_names, self.use_ner)
        for finding in findings:                   # hand out numbers in reading order: the first person is PERSON_1
            self._placeholder(finding)
        return replace_findings(text, findings, self._placeholder)

    def placeholder_for(self, kind, value):
        """Which placeholder stands for this real value? (None if it hasn't been seen.)"""
        return self._lookup.get((kind, re.sub(r"\s", "", value).lower()))

    def restore(self, text):
        """Put real values back. Unknown placeholders (the model invented one) are left as they are."""
        return re.sub(r"<[A-Z_]+_\d+>", lambda m: self.vault.get(m.group(), m.group()), text)

    def export_vault(self, key):
        """The vault encrypted with a Fernet key (AES), safe to store until the conversation ends."""
        import json
        return Fernet(key).encrypt(json.dumps(self.vault).encode())

    def import_vault(self, key, token):
        import json
        self.vault = json.loads(Fernet(key).decrypt(token))
