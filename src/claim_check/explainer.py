"""Turn engine findings into human-readable explanations. The LLM explains; it never decides.

`explain` composes the deterministic engine output with an LLM pass that attaches a plain-English
explanation + suggested fix to each finding (mapped back by index, so the model cannot add or drop
findings) and writes an overall summary. If there are no findings, no model call is made.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from . import prompts
from .client import LLMClient
from .engine import analyze
from .models import CheckResult, Finding


class _Explanation(BaseModel):
    index: int = Field(description="The finding index being explained (0-based, as given).")
    explanation: str = Field(description="Why this matters, in plain English (1-2 sentences).")
    suggested_fix: str = Field(description="A concrete way to fix it.")


class _ExplainerOut(BaseModel):
    explanations: list[_Explanation]
    summary: str = Field(description="1-2 sentence overall summary of the claim set's health.")


def _findings_block(findings: list[Finding]) -> str:
    return "\n".join(
        f"[{i}] claim {f.claim_number} · {f.kind} ({f.severity}): {f.message}"
        for i, f in enumerate(findings)
    )


class ClaimChecker:
    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client

    def check(self, claims_text: str) -> CheckResult:
        claims, findings = analyze(claims_text)
        if not findings:
            return CheckResult(
                claims=claims,
                findings=[],
                summary="No structural issues found — claims parse cleanly with valid antecedent "
                "basis and dependencies.",
            )
        if self._client is None:
            # deterministic-only (no key): return findings without prose
            return CheckResult(claims=claims, findings=findings, summary="")

        out = self._client.structured(
            schema=_ExplainerOut,
            system=prompts.EXPLAINER_SYSTEM,
            user=prompts.explainer_user(claims_text, _findings_block(findings)),
        )
        by_index = {e.index: e for e in out.explanations}
        enriched: list[Finding] = []
        for i, f in enumerate(findings):
            e = by_index.get(i)
            enriched.append(
                f.model_copy(
                    update={
                        "explanation": e.explanation if e else "",
                        "suggested_fix": e.suggested_fix if e else "",
                    }
                )
            )
        return CheckResult(claims=claims, findings=enriched, summary=out.summary)
