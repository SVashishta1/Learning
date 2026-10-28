"""privacy.py: remove personal details BEFORE any text reaches a model, and put them back only locally.

    "My name is Maria Lopez, call me on 0612 345 678"
        -> "My name is [NAME_1], call me on [PHONE_1]"         (this is all a model ever sees)
    The Vault remembers  [NAME_1] = "Maria Lopez"  on YOUR machine, so the final form can be filled in locally.

Rules (regular expressions) catch the common patterns. They are not perfect: names without a clue word
("Maria called") slip through. That is why we also let the user type names in a separate box (known_names),
and why the strictest setting is to run a local model as well (LLM_PROVIDER=ollama + REQUIRE_LOCAL_MODEL=1).
"""
import re

PATTERNS = [   # order matters: the more specific patterns run first
    ("EMAIL", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    ("IDNUM", r"\b\d{3}-\d{2}-\d{4}\b|\b[A-Z]{2}-\d{3}-\d{3}-\d{3}\b"),
    ("DATE", r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b"),
    ("PHONE", r"(?<![\w-])\+?\d[\d ()-]{7,}\d\b"),
    ("ADDRESS", r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Way|Close|Drive|Dr|Calle)\b"),
]
# A capitalised word (or two) right after a clue such as "my name is", "I'm", "my son", "me llamo".
NAME_CLUES = (r"(?:my name is|i am|i'm|this is|named|called|me llamo|mi nombre es|"
              r"my (?:son|daughter|wife|husband|partner|mother|father|mum|mom|dad|child)|"
              r"mi (?:hijo|hija|esposo|esposa|pareja|madre|padre))")
# (?i:...) = ignore case for the clue words only; the name itself must start with a capital letter.
NAME = re.compile("(?i:" + NAME_CLUES + r")\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)")
SELF_INTRO = re.compile(r"(?i:my name is|i am|i'm|this is|me llamo|mi nombre es)\s+(\[NAME_\d+\])")
NOT_NAMES = {"Brightwater", "Working", "Retired", "Unemployed", "Here", "Single", "Not", "From", "Living", "A", "The"}


class Vault:
    """Placeholder <-> real value. Lives only in this process (never sent anywhere)."""

    def __init__(self):
        self.values: dict[str, str] = {}
        self.applicant = ""                     # the placeholder of the person telling the story, if we can tell

    def token_for(self, kind: str, value: str) -> str:
        for token, v in self.values.items():
            if v == value and token.startswith(f"[{kind}_"):
                return token                                       # the same person gets the same token
        token = f"[{kind}_{sum(t.startswith(f'[{kind}_') for t in self.values) + 1}]"
        self.values[token] = value
        return token

    def restore(self, text: str) -> str:
        for token, value in self.values.items():
            text = text.replace(token, value)
        return text


def redact(text: str, vault: Vault, known_names: list[str] | None = None) -> str:
    for name in sorted(known_names or [], key=len, reverse=True):         # names the user typed in a box
        if name.strip():
            text = re.sub(re.escape(name.strip()), vault.token_for("NAME", name.strip()), text, flags=re.IGNORECASE)
    for kind, rx in PATTERNS:
        text = re.sub(rx, lambda m: vault.token_for(kind, m.group(0)), text)

    def name_sub(m):
        name = m.group(1)
        first = name.split()[0]
        if first.capitalize() in NOT_NAMES or not first[0].isupper():
            return m.group(0)
        return m.group(0).replace(name, vault.token_for("NAME", name))
    text = NAME.sub(name_sub, text)
    me = SELF_INTRO.search(text)                  # "my name is [NAME_2]" -> [NAME_2] is the applicant
    if me and not vault.applicant:
        vault.applicant = me.group(1)
    return text


def find_leaks(text: str, vault: Vault) -> list[str]:
    """Which real values from the vault appear in this text? (used by tests and evals)"""
    return [v for v in vault.values.values() if v in text]
