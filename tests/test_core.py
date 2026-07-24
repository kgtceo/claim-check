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


# ── real-claim drafting conventions (added after linting real granted claims) ────────────────

PAGERANK_CLAIMS = (
    "1. A computer implemented method of scoring a plurality of linked documents, comprising: "
    "obtaining a plurality of documents, at least some of the documents being linked documents, "
    "at least some of the documents being linking documents, and at least some of the documents "
    "being both linked documents and linking documents, each of the linked documents being "
    "pointed to by a link in one or more of the linking documents; assigning a score to each of "
    "the linked documents based on scores of the one or more linking documents and processing "
    "the linked documents according to their scores.\n"
    "2. The method of claim 1, wherein the assigning includes: identifying a weighting factor "
    "for each of the linking documents, the weighting factor being dependent on the number of "
    "links to the one or more linking documents, and adjusting the score of each of the one or "
    "more linking documents based on the identified weighting factor.\n"
    "3. The method of claim 1, wherein the assigning includes: identifying a weighting factor "
    "for each of the linking documents, the weighting factor being dependent on an estimation "
    "of a probability that a linking document will be accessed, and adjusting the score of each "
    "of the one or more linking documents based on the identified weighting factor."
)


def test_real_patent_pagerank_claims_are_clean():
    """Claims 1-3 of US 6,285,999 (PageRank, granted 2001, expired) — real granted claim
    language must produce ZERO errors. Each of these once false-positived (dependent-claim
    preamble, gerund step reference, 'the one or more', leading past-participle)."""
    claims, findings = analyze(PAGERANK_CLAIMS)
    assert [(c.number, c.depends_on) for c in claims] == [(1, []), (2, [1]), (3, [1])]
    assert [f for f in findings if f.severity == "error"] == []


def test_dependent_preamble_reference_is_exempt():
    # "The method of claim 1" needs no in-claim antecedent even when the parent's preamble
    # noun is buried behind a participle ("A computer implemented method").
    text = "1. A computer implemented method comprising receiving a signal.\n2. The method of claim 1, wherein the signal is digital."
    assert not [f for f in _errors(text) if f.kind == "antecedent_basis"]


def test_gerund_step_reference_has_basis():
    # "the amplifying" refers to the step "amplifying the signal" in the parent claim.
    text = "1. A method comprising receiving a signal and amplifying the signal.\n2. The method of claim 1, wherein the amplifying is digital."
    assert not [f for f in _errors(text) if f.kind == "antecedent_basis"]


def test_gerund_without_a_step_is_still_flagged():
    text = "1. A method comprising heating a substrate, wherein the mixing is continuous."
    errs = [f for f in _errors(text) if f.kind == "antecedent_basis"]
    assert errs and "mixing" in errs[0].span


def test_quantifier_after_definite_article_is_not_an_element():
    # "the one or more sensors" refers to the sensors, not to an element "one".
    text = "1. A device comprising one or more sensors, wherein the one or more sensors are optical."
    assert not [f for f in _errors(text) if f.kind == "antecedent_basis"]


def test_leading_past_participle_reference_has_basis():
    # "the identified weighting factor" ← "identifying a weighting factor".
    text = "1. A method comprising identifying a weighting factor and adjusting a score based on the identified weighting factor."
    assert not [f for f in _errors(text) if f.kind == "antecedent_basis"]


def test_leading_past_participle_without_base_element_is_still_flagged():
    text = "1. A device comprising a housing, wherein the identified sensor is active."
    assert [f for f in _errors(text) if f.kind == "antecedent_basis"]
