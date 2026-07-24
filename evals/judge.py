"""LLM-as-judge (opus): are the explainer's explanations faithful to the decided findings and do they
suggest a valid fix — without inventing new issues? Separate from the model that wrote them."""

from __future__ import annotations

from pydantic import BaseModel, Field

from claim_check.client import LLMClient
from claim_check.config import Settings
from claim_check.models import CheckResult


class ExplanationGrade(BaseModel):
    faithful: bool = Field(description="Does every explanation match its finding and invent no new issue?")
    actionable: bool = Field(description="Does each suggested_fix concretely address its finding?")
    no_legal_overreach: bool = Field(description="Does it stay drafting-assistance, not legal advice/opinion?")
    comment: str = ""


JUDGE_SYSTEM = (
    "You audit a patent-claim linter's explanations. You are given the DECIDED findings and the "
    "model's explanation + suggested_fix for each. Judge: (1) faithful — each explanation matches its "
    "finding and introduces no new alleged defect; (2) actionable — each fix concretely addresses its "
    "finding; (3) no_legal_overreach — it reads as drafting assistance, not a legal opinion. Be strict."
)


def grade(result: CheckResult, settings: Settings, client: LLMClient | None = None) -> ExplanationGrade:
    client = client or LLMClient(settings)
    block = "\n".join(
        f"- claim {f.claim_number} · {f.kind}: FINDING={f.message} | EXPLANATION={f.explanation} "
        f"| FIX={f.suggested_fix}"
        for f in result.findings
    ) or "(none)"
    user = f"SUMMARY: {result.summary}\n\nFINDINGS + EXPLANATIONS:\n{block}"
    return client.structured(schema=ExplanationGrade, system=JUDGE_SYSTEM, user=user, model=settings.judge_model)
