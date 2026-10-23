import pytest

from skills_check import SKILLS, parse_answers, report, study_plan


def test_parse_answers_accepts_twelve_numbers():
    assert parse_answers("3,2,1,0,0,1,0,0,1,0,0,0") == [3, 2, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0]


def test_parse_answers_rejects_wrong_count_and_bad_numbers():
    with pytest.raises(ValueError, match="exactly 12"):
        parse_answers("1,2,3")
    with pytest.raises(ValueError, match="0, 1, 2 or 3"):
        parse_answers("4," + ",".join(["1"] * 11))


def test_plan_keeps_only_weak_skills_in_learning_order():
    scores = [3, 3, 1, 3, 0, 3, 3, 3, 3, 3, 3, 1]
    plan = study_plan(scores)
    assert [name for name, _, _ in plan] == ["LLM apps", "Linux and the terminal",
                                             "Agents and deployment at the customer"]


def test_report_when_everything_is_strong():
    text = report([3] * len(SKILLS))
    assert "100% of the way" in text
    assert "capstones" in text
