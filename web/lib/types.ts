// Mirrors the backend Pydantic models (claim_check.models).

export type ClaimKind = "independent" | "dependent";

export type FindingKind =
  | "antecedent_basis"
  | "dependency"
  | "single_sentence"
  | "indefiniteness";

export type Severity = "error" | "advisory";

export interface Claim {
  number: number;
  text: string;
  kind: ClaimKind;
  depends_on: number[];
}

export interface Finding {
  claim_number: number;
  kind: FindingKind;
  severity: Severity;
  element: string | null;
  span: string;
  message: string;
  explanation: string;
  suggested_fix: string;
}

export interface CheckResult {
  claims: Claim[];
  findings: Finding[];
  summary: string;
}

// Sample claim sets keyed by name: { [name]: claimsText }
export type SamplesResponse = Record<string, string>;
