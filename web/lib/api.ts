import { FALLBACK_SAMPLES } from "./samples";
import type { CheckResult, Sample, SamplesResponse } from "./types";

// Strip any trailing slash so `${API_URL}/api/...` never becomes `...//api/...` (404).
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

// Never rejects: falls back to the baked-in samples when the API is cold or the
// response isn't the expected shape, so "Load example" always works.
export async function fetchSamples(): Promise<SamplesResponse> {
  try {
    const res = await fetch(`${API_URL}/api/samples`);
    if (!res.ok) throw new Error(`status ${res.status}`);
    const body = await res.json();
    const ok =
      Array.isArray(body?.samples) &&
      body.samples.length > 0 &&
      body.samples.every((s: Sample) => typeof s?.claims === "string" && typeof s?.name === "string");
    if (!ok) throw new Error("unexpected samples shape");
    return body as SamplesResponse;
  } catch {
    return { samples: FALLBACK_SAMPLES };
  }
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
