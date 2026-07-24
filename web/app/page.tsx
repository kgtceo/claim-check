"use client";

import { useEffect, useRef, useState } from "react";
import { checkClaims, fetchSamples } from "../lib/api";
import { FALLBACK_SAMPLES } from "../lib/samples";
import type { CheckResult, Finding, Sample } from "../lib/types";

const PLACEHOLDER = `1. A device comprising:
   a housing;
   a processor disposed within the housing; and
   a sensor coupled to the processor.
2. The device of claim 1, wherein the sensor comprises a temperature sensor.
3. The device of claim 1, further comprising a wireless transceiver coupled to the processor.`;

function FindingCard({ f }: { f: Finding }) {
  return (
    <div className={`finding ${f.severity}`}>
      <div className="fhead">
        <span className="claimno">Claim {f.claim_number}</span>
        <span className="sev">{f.severity}</span>
        <span className="kind">{f.kind.replace(/_/g, " ")}</span>
      </div>
      <p className="fmsg">
        {f.message}
        {f.span ? <> — <span className="span">&ldquo;{f.span}&rdquo;</span></> : null}
      </p>
      {f.explanation && (
        <p className="sub"><span className="lbl">why:</span>{f.explanation}</p>
      )}
      {f.suggested_fix && (
        <p className="sub"><span className="lbl">fix:</span>{f.suggested_fix}</p>
      )}
    </div>
  );
}

export default function Home() {
  // Seeded with the baked-in samples so "Load example" is tappable immediately,
  // even while the backend is still cold-starting.
  const [samples, setSamples] = useState<Sample[]>(FALLBACK_SAMPLES);
  const [text, setText] = useState("");
  const [result, setResult] = useState<CheckResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSamples()
      .then((r) => setSamples(r.samples))
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load samples."));
  }, []);

  const exampleIdx = useRef(0);

  function loadExample() {
    if (samples.length === 0) return;
    const s = samples[exampleIdx.current % samples.length];
    exampleIdx.current += 1;
    setText(s.claims);
    setResult(null);
    setError(null);
  }

  async function check() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await checkClaims(text));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const errors = result ? result.findings.filter((f) => f.severity === "error").length : 0;
  const advisory = result ? result.findings.filter((f) => f.severity === "advisory").length : 0;

  return (
    <div className="container">
      <header>
        <h1>claim-check — patent claim structure &amp; antecedent-basis linter</h1>
        <p>
          Paste a numbered claim set and get a heuristic structural review: claim dependencies,
          antecedent-basis gaps, single-sentence form and indefiniteness flags.
        </p>
      </header>

      <div className="banner">
        ⚠️ Educational — heuristic linter, <strong>not legal advice</strong>.
      </div>

      <label htmlFor="claims">Patent claim set</label>
      {samples.length > 0 && (
        <div className="samples">
          {samples.map((s) => (
            <button
              key={s.name}
              onClick={() => { setText(s.claims); setResult(null); setError(null); }}
            >
              {s.name}
              {s.tag && <span className="sample-tag">{s.tag}</span>}
            </button>
          ))}
        </div>
      )}
      <textarea
        id="claims"
        value={text}
        placeholder={PLACEHOLDER}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="actions">
        <button className="primary" onClick={check} disabled={loading || !text.trim()}>
          {loading ? "Checking…" : "Check claims"}
        </button>
        <button onClick={loadExample} disabled={loading || samples.length === 0}>
          Load example
        </button>
        <span className="hint">(first run ~5–10s)</span>
      </div>

      {error && <div className="error">{error}</div>}

      {result && (
        <>
          <p className="result-head">
            Parsed {result.claims.length} claim{result.claims.length === 1 ? "" : "s"} —{" "}
            <span className="err">{errors} error{errors === 1 ? "" : "s"}</span>,{" "}
            <span className="adv">{advisory} advisory</span>
          </p>

          {result.findings.length === 0 ? (
            <div className="clean">✓ No structural issues found.</div>
          ) : (
            result.findings.map((f, i) => <FindingCard key={i} f={f} />)
          )}

          {result.summary && (
            <div className="panel">
              <h2>Summary</h2>
              <div className="summary">{result.summary}</div>
            </div>
          )}
        </>
      )}

      <p className="disc">
        claim-check is an educational heuristic linter for the structure of patent claims. It does
        not perform prior-art search or novelty/obviousness analysis and is not legal advice.
      </p>
    </div>
  );
}
