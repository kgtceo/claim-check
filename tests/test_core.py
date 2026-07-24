"""Offline tests for the deterministic engine — no API key, no network."""

from __future__ import annotations

from claim_check.engine import analyze, parse_claims
from claim_check.explainer import ClaimChecker


def _errors(text):
    _, findings = analyze(text)
    return [f for f in findings if f.severity == "error"]


def _kinds(text):
    return {f.kind for f in _errors(text)}


def test_parses_independent_and_dependent():
    claims = parse_claims(
        "1. A device comprising a widget.\n2. The device of claim 1, wherein the widget is round."
    )
    assert [c.kind for c in claims] == ["independent", "dependent"]
    assert claims[1].depends_on == [1]


def test_clean_claims_have_no_errors():
    text = (
        "1. An apparatus comprising: a processor; a memory storing instructions; and a network "
        "interface, wherein the processor transmits a record via the network interface.\n"
        "2. The apparatus of claim 1, wherein the processor comprises a first core and a second core."
    )
    assert _errors(text) == []


def test_missing_antecedent_is_caught():
    text = "1. A device comprising a processor and a memory coupled to the controller."
    kinds = _kinds(text)
    assert "antecedent_basis" in kinds


def test_housing_ing_noun_is_not_a_false_positive():
    text = (
        "1. A widget comprising a base and a housing coupled to the base, wherein the housing "
        "supports a lid."
    )
    assert _errors(text) == []


def test_shortened_reference_matches_full_element():
    text = "1. A widget assembly comprising a base and a housing, wherein the assembly is sealed."
    assert _errors(text) == []


def test_forward_and_self_dependency_are_caught():
    assert "dependency" in _kinds("1. A thing comprising a part.\n2. The thing of claim 5.")
    assert "dependency" in _kinds("1. A thing comprising a part.\n2. The thing of claim 2.")


def test_broken_dependency_suppresses_antecedent_cascade():
    # claim 2 depends on a non-existent claim 5, so its definite refs should NOT cascade errors
    text = "1. A sensor comprising a photodiode.\n2. The sensor of claim 5, wherein the photodiode is planar."
    errs = _errors(text)
    assert len(errs) == 1 and errs[0].kind == "dependency"


def test_multi_sentence_is_caught():
    assert "single_sentence" in _kinds("1. A gadget comprising a widget. The widget is blue.")


def test_indefiniteness_is_advisory_not_error():
    _, findings = analyze("1. A device comprising a substantially planar plate.")
    advisories = [f for f in findings if f.kind == "indefiniteness"]
    assert advisories and all(f.severity == "advisory" for f in advisories)


def test_explainer_without_client_returns_findings_offline():
    # no API key needed: the checker returns engine findings with empty prose
    result = ClaimChecker(client=None).check(
        "1. A device comprising a processor coupled to the controller."
    )
    assert result.error_count >= 1
