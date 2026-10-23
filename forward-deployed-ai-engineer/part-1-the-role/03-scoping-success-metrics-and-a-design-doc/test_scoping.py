from pathlib import Path

import pytest

from lint_design_doc import lint
from value_calculator import apply_overrides, calculate, load

HERE = Path(__file__).parent


def northwind():
    return load(HERE / "northwind_assumptions.json")


def test_northwind_numbers_add_up():
    r = calculate(northwind())
    assert round(r["tickets"]) == 15_600                 # 9,000 a week x 52/12 x 40%
    assert r["cost_per_ticket"] == pytest.approx(0.032)  # 6,000 x $4/M + 400 x $20/M
    assert round(r["hours_saved"]) == 728                # 15,600 x 70% x 4 min / 60
    assert round(r["break_even_months"], 1) == 4.4


def test_halving_acceptance_halves_the_time_saved():
    full = calculate(northwind())["hours_saved"]
    half = calculate(apply_overrides(northwind(), ["acceptance_rate=0.35"]))["hours_saved"]
    assert half == pytest.approx(full / 2)


def test_never_breaks_even_when_costs_exceed_value():
    v = apply_overrides(northwind(), ["acceptance_rate=0", "model=claude-opus-5-5"])
    assert calculate(v)["break_even_months"] is None


def test_unknown_assumption_is_refused():
    with pytest.raises(KeyError):
        apply_overrides(northwind(), ["acceptance=1"])


def test_filled_example_passes_and_template_fails():
    errors, warnings = lint((HERE / "northwind_design_doc.md").read_text())
    assert errors == [] and warnings == []
    errors, _ = lint((HERE / "design_doc_template.md").read_text())
    assert "Empty section: '## Summary'" in errors


def test_linter_catches_classic_mistakes():
    doc = (HERE / "northwind_design_doc.md").read_text()
    doc = doc.replace("| under 2 min |", "| much faster |")                     # target without a number
    doc = doc.replace("| Tomasz |", "| |")                                      # risk without an owner
    doc = doc.replace("- Cut agent handling time", "- Make support better and cut agent handling time")
    errors, warnings = lint(doc)
    assert "Success metrics: 'Agent handling time per WISMO ticket' target has no number" in errors
    assert "Risks: 'Firewall rule for TMS replica is late' has no owner" in errors
    assert any("vague word 'better'" in w for w in warnings)
