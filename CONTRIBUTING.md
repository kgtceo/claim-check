# Contributing

Thanks for looking! This is an educational demo, but issues and PRs are welcome — **the most useful
contribution is more eval cases**, because that's what makes the linter trustworthy.

## Run it locally

```bash
pip install -e .
pip install pytest
pytest -q                 # offline — no API key needed
python evals/run_evals.py # deterministic eval gates — also no API key needed
```

CI runs `pytest -q` and the eval gates on every push; keep them green.

## Add an eval case (most valuable)

Add one JSON object to `evals/dataset/cases.json`:

```json
{ "name": "my-case",
  "claims": "1. A device comprising a widget coupled to the controller.",
  "expect_errors": [{ "claim_number": 1, "kind": "antecedent_basis" }] }
```

`kind` ∈ `antecedent_basis` · `dependency` · `single_sentence` · `indefiniteness`; use
`"expect_errors": []` for a clean set. Good cases to add: **real-world edge cases** the heuristic
struggles with — unusual multiple-dependent chains, EPO-style formatting, means-plus-function claims.

## Add a new check to the engine (advanced)

All defect detection lives in `src/claim_check/engine.py` — no LLM. To add a new `kind` (e.g.
`means_plus_function`):

1. Add the literal to `FindingKind` in `src/claim_check/models.py`.
2. Write a `_check_<kind>(claim, ...) -> list[Finding]` in `engine.py` (return `Finding`s with a
   verbatim `span` so the grounding gate passes).
3. Call it from `check()` alongside the existing checks.
4. Add labelled cases to `evals/dataset/cases.json` and keep `pytest -q` + `run_evals.py` green.

The LLM only ever *explains* findings — new detection logic stays deterministic.

## Guidelines

- Use **synthetic or public** patent text only — never confidential drafts.
- Keep the framing: this is a heuristic drafting linter, **not legal advice**.
- Keep PRs small and focused; `pytest -q` must stay green.
