"""claim-check — a patent-claim structure & antecedent-basis linter.

A DETERMINISTIC engine parses a claim set and decides the structural defects (lack of antecedent
basis, bad claim dependencies, multi-sentence claims, relative-term indefiniteness). The LLM never
decides a defect — it only explains each finding in plain English and suggests a fix. Ships an eval
harness scoring recall / precision / grounding on planted-error claim sets.

EDUCATIONAL — a heuristic linter, NOT legal advice."""

from .client import LLMClient
from .config import Settings
from .engine import analyze, check, parse_claims
from .models import Claim, CheckResult, Finding

__all__ = [
    "LLMClient",
    "Settings",
    "analyze",
    "check",
    "parse_claims",
    "Claim",
    "CheckResult",
    "Finding",
]
