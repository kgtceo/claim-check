"""Typed contracts for claim-check.

A patent claim set is parsed into `Claim`s. A deterministic engine produces `Finding`s (the
engine DECIDES; the LLM never invents a defect). The LLM then attaches a plain-English
`explanation` + `suggested_fix` to each finding — it explains, it does not decide.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FindingKind = Literal["antecedent_basis", "dependency", "single_sentence", "indefiniteness"]
Severity = Literal["error", "advisory"]


class Claim(BaseModel):
    number: int = Field(description="The claim number as written.")
    text: str = Field(description="The full verbatim claim text.")
    kind: Literal["independent", "dependent"]
    depends_on: list[int] = Field(default_factory=list, description="Claim numbers this one depends on (empty if independent).")


class Finding(BaseModel):
    claim_number: int
    kind: FindingKind
    severity: Severity
    element: str | None = Field(default=None, description="The offending claim element/term, if applicable.")
    span: str = Field(description="A verbatim span from the claim that the finding is about (grounding).")
    message: str = Field(description="Deterministic, engine-generated description of the issue.")
    # Filled in by the LLM explainer (it explains; it never decides a finding exists):
    explanation: str = Field(default="", description="Plain-English explanation of why this matters.")
    suggested_fix: str = Field(default="", description="A concrete way to fix it.")


class CheckResult(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    summary: str = Field(default="", description="One-paragraph overview drafted by the LLM from the findings.")

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def advisory_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "advisory")
