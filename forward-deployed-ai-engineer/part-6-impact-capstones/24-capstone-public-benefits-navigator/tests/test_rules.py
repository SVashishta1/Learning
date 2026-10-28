"""The rules engine and the policy corpus. Code calculates; these tests make sure it calculates right."""
import re

import pytest

from benefits_tools import PROGRAMMES, PolicyIndex, Profile, check_all, documents_for, income_limit, reading_grade


@pytest.mark.parametrize("programme", list(PROGRAMMES))
def test_prose_limits_match_the_rules_file(programme):
    """The numbers written in each policy .md must equal what the code computes (no silent drift)."""
    text = open(f"policies/{programme}.md", encoding="utf-8").read()
    written = [int(n.replace(",", "")) for n in re.findall(r"(\d,\d{3}) for (?:a household of )?\d", text)]
    assert written == [income_limit(programme, size) for size in (1, 2, 3, 4)]


def family(**kw):
    base = dict(household_size=2, members=[{"role": "adult", "works_or_studies": True}, {"role": "child", "age": 2}],
                monthly_income=1450, monthly_rent=700, county_resident=True)
    return Profile(**{**base, **kw})


def test_statuses_for_a_single_parent():
    res = check_all(family())
    assert {k: v["status"] for k, v in res.items()} == {
        "foodbridge": "likely", "kidcare": "likely", "warmhome": "maybe", "rentrelief": "likely",
        "childcare": "likely", "schoolmeals": "unlikely"}


def test_one_failed_criterion_makes_it_unlikely_and_unknown_makes_it_maybe():
    assert check_all(family(monthly_income=9000))["foodbridge"]["status"] == "unlikely"
    assert check_all(family(monthly_income=None))["foodbridge"]["status"] == "maybe"


def test_school_meals_without_income_test_when_foodbridge_is_likely():
    p = family(members=[{"role": "adult", "works_or_studies": True}, {"role": "child", "age": 8}])
    assert check_all(p)["schoolmeals"]["criteria"][-1]["detail"].startswith("household is likely to get FoodBridge")


def test_search_finds_the_right_section():
    hit = PolicyIndex().search("heating bill energy company winter")[0]
    assert hit["programme"] == "warmhome"


def test_documents_are_merged_across_programmes():
    rows = documents_for(["foodbridge", "kidcare", "rentrelief"])
    assert rows[0]["document"] == "proof_of_income" and rows[0]["for"] == ["foodbridge", "kidcare", "rentrelief"]


def test_reading_grade():
    assert reading_grade("You may get help. Bring your papers.") < 4
    assert reading_grade("Notwithstanding aforementioned considerations, eligibility determinations "
                         "necessitate comprehensive documentation verification.") > 12
