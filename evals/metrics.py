"""Deterministic eval metrics over the engine's findings — no model calls."""

from __future__ import annotations

from claim_check.models import CheckResult, Finding


def _error_keys(findings: list[Finding]) -> set[tuple[int, str]]:
    return {(f.claim_number, f.kind) for f in findings if f.severity == "error"}


def recall_ok(findings: list[Finding], expected: list[dict]) -> bool:
    """Every planted (claim, kind) error is caught."""
    got = _error_keys(findings)
    return all((e["claim_number"], e["kind"]) in got for e in expected)


def precision_ok(findings: list[Finding], expected: list[dict]) -> bool:
    """No error-severity finding beyond the planted set (no crying wolf; clean claims stay quiet)."""
    exp = {(e["claim_number"], e["kind"]) for e in expected}
    return not [k for k in _error_keys(findings) if k not in exp]


def grounded(result: CheckResult) -> bool:
    """Every finding's span actually appears in its claim's text (no fabricated quotes)."""
    norm = lambda s: " ".join(s.lower().split())
    text_by_claim = {c.number: norm(c.text) for c in result.claims}
    for f in result.findings:
        if not f.span:
            continue
        if norm(f.span) not in text_by_claim.get(f.claim_number, ""):
            return False
    return True
