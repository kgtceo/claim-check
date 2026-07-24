# Deploy

Two pieces: the FastAPI backend (Railway) and the Next.js UI (Vercel).

## Backend → Railway
1. New project from this repo. Railway builds the `Dockerfile`.
2. Env vars: `ANTHROPIC_API_KEY`, and `CK_CORS_ORIGINS=https://claim-check.kareemghazal.com` (your UI origin).
3. **Generate Domain** → set the target port to match the deploy log's `Uvicorn running on 0.0.0.0:<port>` line.
4. Verify: `GET /health` returns `{"status":"ok"}`.

## Frontend → Vercel
1. New project, **root directory = `web`**.
2. Env var `NEXT_PUBLIC_API_URL` = the Railway URL (bakes in at build time — redeploy after changing it).
3. Deploy. Optionally attach `claim-check.kareemghazal.com` and add that origin to `CK_CORS_ORIGINS`.

## Notes
- `NEXT_PUBLIC_API_URL` is read at build time; trailing slash is stripped in `web/lib/api.ts`.
- The deterministic engine needs no key; only the LLM explanations do.
