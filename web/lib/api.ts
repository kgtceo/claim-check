import type { CheckResult, SamplesResponse } from "./types";

// Strip any trailing slash so `${API_URL}/api/...` never becomes `...//api/...` (404).
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export async function fetchSamples(): Promise<SamplesResponse> {
  const res = await fetch(`${API_URL}/api/samples`);
  if (!res.ok) throw new Error(`Could not load samples (${res.status})`);
  return res.json();
}

export async function checkClaims(claims: string): Promise<CheckResult> {
  const res = await fetch(`${API_URL}/api/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claims }),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}
