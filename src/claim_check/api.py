"""FastAPI wrapper: POST a claim set, get parsed claims + linter findings (with explanations)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .data.sample_claims import SAMPLE_CLAIMS, SAMPLE_TAGS
from .explainer import ClaimChecker
from .models import CheckResult

app = FastAPI(title="claim-check", version="1.0.0")

_origins = [o.strip() for o in os.getenv("CK_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,  # explicit prod origins via CK_CORS_ORIGINS (e.g. the custom domain)
    allow_origin_regex=r"https://claim-check[a-z0-9-]*\.vercel\.app|http://localhost:3000",
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckRequest(BaseModel):
    claims: str


_checker: ClaimChecker | None = None


def _get_checker() -> ClaimChecker:
    global _checker
    if _checker is None:
        from .client import LLMClient
        from .config import Settings

        _checker = ClaimChecker(LLMClient(Settings.from_env()))
    return _checker


@app.get("/api/samples")
def samples() -> dict:
    return {
        "samples": [
            {"name": name, "claims": claims, "tag": SAMPLE_TAGS.get(name, "")}
            for name, claims in SAMPLE_CLAIMS.items()
        ]
    }


@app.post("/api/check", response_model=CheckResult)
def check(req: CheckRequest) -> CheckResult:
    if not req.claims or not req.claims.strip():
        raise HTTPException(status_code=400, detail="No claim text provided.")
    try:
        return _get_checker().check(req.claims)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
