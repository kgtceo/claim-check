"""Run the claim-check eval suite.

Deterministic gates (no API key, always run):
  • RECALL     — every planted structural error (antecedent basis / dependency / single-sentence) is caught.
  • PRECISION  — clean claim sets stay quiet; no error beyond the planted set.
  • GROUNDING  — every finding's span really appears in its claim text (no fabricated quotes).
Optional (needs a key, --judge): run the LLM explainer + an opus judge on explanation faithfulness.

Every run writes a reproducible artifact to evals/results/latest.json (per-case outcomes,
models used when --judge runs, timestamp) — the numbers quoted in the README come from that file.

    python evals/run_evals.py             # deterministic gates only (no key needed)
    python evals/run_evals.py --judge     # + LLM explanations + opus judge
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from claim_check.engine import analyze
from claim_check.models import CheckResult

from metrics import grounded, precision_ok, recall_ok  # noqa: E402

DATASET = Path(__file__).parent / "dataset" / "cases.json"
RESULTS = Path(__file__).parent / "results" / "latest.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true", help="Also run the LLM explainer + opus judge (needs API key).")
    args = ap.parse_args()

    cases = json.loads(DATASET.read_text())
    failures: list[str] = []
    per_case: list[dict] = []
    total_expected = 0
    total_caught = 0

    for case in cases:
        claims, findings = analyze(case["claims"])
        result = CheckResult(claims=claims, findings=findings)
        expected = case.get("expect_errors", [])
        total_expected += len(expected)
        rec, prec, gnd = recall_ok(findings, expected), precision_ok(findings, expected), grounded(result)
        if rec:
            total_caught += len(expected)
        errs = [f for f in findings if f.severity == "error"]
        print(f"\n=== {case['name']} ===")
        print(f"  errors={len(errs)} expected={len(expected)}  RECALL={'✓' if rec else '✗'} "
              f"PRECISION={'✓' if prec else '✗'} GROUNDED={'✓' if gnd else '✗'}")
        for f in errs:
            print(f"    [{f.kind}] cl{f.claim_number}: {f.element}")
        if not rec:
            failures.append(f"{case['name']}: missed a planted error (recall)")
        if not prec:
            failures.append(f"{case['name']}: flagged an unexpected error (precision)")
        if not gnd:
            failures.append(f"{case['name']}: a finding quotes a span not in the claim (grounding)")

        per_case.append({
            "name": case["name"],
            "source": case.get("source"),
            "errors_found": len(errs),
            "errors_expected": len(expected),
            "recall_ok": rec,
            "precision_ok": prec,
            "grounded": gnd,
        })

    judge_results: list[dict] = []
    settings = None
    if args.judge:
        from claim_check.client import LLMClient
        from claim_check.config import Settings
        from claim_check.explainer import ClaimChecker
        from judge import grade  # noqa: E402

        settings = Settings.from_env()
        client = LLMClient(settings)
        checker = ClaimChecker(client)
        print("\n--- LLM explanation judge (opus) ---")
        for case in cases:
            if not case.get("expect_errors"):
                continue
            result = checker.check(case["claims"])
            g = grade(result, settings, client)
            print(f"  {case['name']}: faithful={g.faithful} actionable={g.actionable} "
                  f"no_overreach={g.no_legal_overreach}")
            judge_results.append({"name": case["name"], **g.model_dump()})
            if not (g.faithful and g.actionable and g.no_legal_overreach):
                failures.append(f"{case['name']}: judge flagged the explanations")

    artifact = {
        "run": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "engine": "deterministic (no LLM)",
            "explainer_model": settings.model if settings else None,
            "judge_model": settings.judge_model if settings else None,
            "dataset_size": len(cases),
        },
        "metrics": {
            "planted_errors_caught": f"{total_caught}/{total_expected}",
            "judge_pass": f"{sum(1 for j in judge_results if j['faithful'] and j['actionable'] and j['no_legal_overreach'])}/{len(judge_results)}" if judge_results else None,
            "all_gates_passed": not failures,
        },
        "failures": failures,
        "per_case": per_case,
        "judge": judge_results or None,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"\nWrote {RESULTS.relative_to(Path(__file__).parent.parent)}")

    print("\n" + "=" * 44)
    print(f"RECALL: {total_caught}/{total_expected} planted errors caught")
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("ALL GATES PASSED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
