"""benefits_tools.py: the facts of the (FICTIONAL) Brightwater County benefits, in plain Python.

  PolicyIndex   splits the policy documents into sections and finds the best ones for a question (BM25)
  check_rules   the income maths and yes/no rules, criterion by criterion: code calculates, the model explains
  forms         which fields each form needs, filled with placeholders like [NAME_1] (never real names)
  readability   a reading-grade score, so explanations stay plain
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

HERE = Path(__file__).parent
RULES = json.loads((HERE / "policies" / "rules.json").read_text(encoding="utf-8"))
PROGRAMMES = RULES["programmes"]


# ---------------------------------------------------------------- the household (what intake fills in)
class Member(BaseModel):
    role: str = Field(description="adult or child")
    age: int | None = None
    in_school: bool | None = Field(default=None, description="children: goes to school?")
    works_or_studies: bool | None = Field(default=None, description="adults: works or studies?")


class Profile(BaseModel):
    household_size: int = Field(ge=1, le=20)
    members: list[Member]
    monthly_income: float | None = Field(default=None, description="Gross monthly income of the whole household")
    monthly_rent: float | None = Field(default=None, description="0 if they own or live free; null if unknown")
    pays_heating: bool | None = None
    county_resident: bool | None = None
    eviction_notice: bool | None = None
    preferred_language: str = "en"


# ---------------------------------------------------------------- retrieval: BM25 over policy sections
def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class PolicyIndex:
    def __init__(self, folder: Path = HERE / "policies"):
        self.chunks = []
        for path in sorted(folder.glob("*.md")):
            programme = path.stem
            for section in re.split(r"\n(?=## )", path.read_text(encoding="utf-8")):
                if section.startswith("## "):
                    title = section.splitlines()[0][3:].strip()
                    slug = re.sub(r"[^a-z]+", "-", title.lower()).strip("-")
                    self.chunks.append({"chunk_id": f"{programme}#{slug}", "programme": programme,
                                        "section": title, "text": " ".join(section.splitlines()[1:]).strip()})
        self.tokens = [_words(c["section"] + " " + c["text"]) for c in self.chunks]
        self.avg_len = sum(map(len, self.tokens)) / len(self.tokens)
        self.df = Counter(w for toks in self.tokens for w in set(toks))

    def search(self, query: str, programme: str | None = None, k: int = 4) -> list[dict]:
        """BM25: words that are rare across documents and frequent in this section score highest."""
        q, n, scored = _words(query), len(self.chunks), []
        for chunk, toks in zip(self.chunks, self.tokens):
            if programme and chunk["programme"] != programme:
                continue
            tf, score = Counter(toks), 0.0
            for w in q:
                if w in tf:
                    idf = math.log(1 + (n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    score += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(toks) / self.avg_len))
            if score > 0:
                scored.append({**chunk, "score": round(score, 2)})
        return sorted(scored, key=lambda c: -c["score"])[:k]

    def ids(self) -> set[str]:
        return {c["chunk_id"] for c in self.chunks}


# ---------------------------------------------------------------- rules: code calculates
def bbna(size: int) -> int:
    t = RULES["bbna"]
    return t[str(size)] if str(size) in t else t["4"] + (size - 4) * t["extra_person"]


def income_limit(programme: str, size: int) -> float:
    return round(bbna(size) * PROGRAMMES[programme]["income_pct"] / 100)


def _criterion(name, result, detail, chunk):
    return {"criterion": name, "result": result, "detail": detail, "source": chunk}


def check_rules(programme: str, p: Profile, foodbridge_likely: bool = False) -> dict:
    """Every criterion -> pass / fail / unknown. Any fail -> unlikely; any unknown -> maybe; else likely."""
    if programme not in PROGRAMMES:
        raise KeyError(f"Unknown programme {programme}. Known: {list(PROGRAMMES)}")
    rule, out = PROGRAMMES[programme], []
    who = f"{programme}#who-can-get-it"
    children = [m for m in p.members if m.role == "child"]
    adults = [m for m in p.members if m.role == "adult"]
    for need in rule["needs"]:
        if need == "resident":
            r = {True: "pass", False: "fail", None: "unknown"}[p.county_resident]
            out.append(_criterion("lives in Brightwater County", r, f"county_resident = {p.county_resident}", who))
        elif need in ("child_under_19", "child_under_13"):
            limit = 19 if need.endswith("19") else 13
            ages = [m.age for m in children]
            r = "pass" if any(a is not None and a < limit for a in ages) else ("unknown" if None in ages else "fail")
            out.append(_criterion(f"has a child under {limit}", r, f"children's ages: {ages or 'none'}", who))
        elif need == "child_in_school":
            school = [m.in_school if m.in_school is not None else (5 <= (m.age or 0) <= 18) for m in children]
            r = "pass" if any(school) else "fail"
            out.append(_criterion("has a child aged 5-18 in school", r, f"in school: {school or 'no children'}", who))
        elif need == "pays_heating":
            r = {True: "pass", False: "fail", None: "unknown"}[p.pays_heating]
            out.append(_criterion("pays a heating/energy bill", r, f"pays_heating = {p.pays_heating}", who))
        elif need == "rent_over_40pct":
            if p.monthly_rent is None or not p.monthly_income:
                r, d = "unknown", "rent or income unknown"
            else:
                share = p.monthly_rent / p.monthly_income
                r, d = ("pass" if share > 0.40 else "fail"), f"rent {p.monthly_rent:.0f} is {share:.0%} of income"
            out.append(_criterion("rent is more than 40% of income", r, d, who))
        elif need == "all_adults_work_or_study":
            flags = [m.works_or_studies for m in adults]
            r = "fail" if False in flags else ("unknown" if None in flags or not flags else "pass")
            out.append(_criterion("every adult works or studies", r, f"adults working/studying: {flags}", who))
    limit = income_limit(programme, p.household_size)
    if programme == "schoolmeals" and foodbridge_likely:
        out.append(_criterion("income test", "pass", "household is likely to get FoodBridge (no income test needed)", who))
    elif p.monthly_income is None:
        out.append(_criterion("income at or below the limit", "unknown", f"income unknown; limit {limit:.0f}",
                              f"{programme}#income-limit"))
    else:
        r = "pass" if p.monthly_income <= limit else "fail"
        out.append(_criterion("income at or below the limit", r,
                              f"income {p.monthly_income:.0f} vs limit {limit:.0f} for {p.household_size} people "
                              f"({rule['income_pct']}% of BBNA {bbna(p.household_size)})", f"{programme}#income-limit"))
    results = [c["result"] for c in out]
    status = "unlikely" if "fail" in results else ("maybe" if "unknown" in results else "likely")
    return {"programme": programme, "name": rule["name"], "status": status, "criteria": out}


def check_all(p: Profile) -> dict[str, dict]:
    res = {k: check_rules(k, p) for k in PROGRAMMES if k != "schoolmeals"}
    res["schoolmeals"] = check_rules("schoolmeals", p, foodbridge_likely=res["foodbridge"]["status"] == "likely")
    return res


# ---------------------------------------------------------------- documents and forms
def documents_for(programmes: list[str]) -> list[dict]:
    """One row per document, listing every programme it serves (bring it once, use it many times)."""
    rows: dict[str, dict] = {}
    for prog in programmes:
        for doc in PROGRAMMES[prog]["documents"]:
            rows.setdefault(doc, {"document": doc, "label": RULES["documents"][doc], "for": []})["for"].append(prog)
    return sorted(rows.values(), key=lambda r: -len(r["for"]))


FIELD_SOURCES = {"applicant_name": "placeholder [NAME_n] of the adult applying", "address": "placeholder [ADDRESS_n]",
                 "phone": "placeholder [PHONE_n]", "household_size": "profile", "monthly_income": "profile",
                 "monthly_rent": "profile", "children_ages": "profile",
                 "energy_company": "ask the family", "landlord_name": "ask the family", "school_names": "ask the family"}


def form_template(programme: str) -> dict:
    rule = PROGRAMMES[programme]
    return {"programme": programme, "form": rule["form"],
            "fields": [{"field": f, "fill_from": FIELD_SOURCES[f]} for f in rule["form_fields"]]}


# ---------------------------------------------------------------- readability
def _syllables(word: str) -> int:
    groups = re.findall(r"[aeiouy]+", word.lower())
    return max(1, len(groups) - (1 if word.lower().endswith("e") and len(groups) > 1 else 0))


def reading_grade(text: str) -> float:
    """Flesch-Kincaid grade level (English): about the school year needed to read it easily. Aim for 8 or less."""
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    syll = sum(_syllables(w) for w in words)
    return round(0.39 * len(words) / sentences + 11.8 * syll / len(words) - 15.59, 1)
