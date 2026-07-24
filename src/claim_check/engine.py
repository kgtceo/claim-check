"""The deterministic claim-checking engine — no LLM, no network.

It parses a patent claim set and DECIDES the structural defects a drafter must not get wrong:

  • antecedent_basis — a definite reference ("the X" / "said X") with no earlier introduction
    ("a X" / "an X" / "at least one X") in the claim or its dependency chain. The classic §112 defect.
  • dependency      — a dependent claim that references a later / non-existent / itself claim number.
  • single_sentence — a claim written as more than one sentence (a formality requirement).
  • indefiniteness  — relative terms of degree ("substantially", "about", "preferably"...) that
    often draw a §112(b) indefiniteness objection (advisory — a human should judge).

This is a heuristic linter, not a legal determination. Element detection is a controlled
token-walk (not greedy regex): after an article we take the noun-phrase head up to a stop word or a
participle. It is deliberately conservative — skips patent boilerplate, matches on the NP head, and
stays quiet on a claim whose dependency is already broken — to avoid crying wolf. The LLM never runs
here; it only explains these findings afterwards.
"""

from __future__ import annotations

import re

from .models import Claim, Finding

# ── parsing ────────────────────────────────────────────────────────────────────────────────

_CLAIM_START = re.compile(r"(?m)^\s*(\d+)\.\s+")
_DEP_REF = re.compile(
    r"\b(?:of|to|in|according to|as (?:recited|claimed|defined|set forth) in|as in)\s+"
    r"claims?\s+\d+(?:\s*(?:-|–|to|and|or|,)\s*\d+)*",
    re.IGNORECASE,
)
_DEP_NUM = re.compile(r"\d+")


def parse_claims(text: str) -> list[Claim]:
    """Split a numbered claim set into Claims and resolve each one's dependencies."""
    marks = list(_CLAIM_START.finditer(text))
    claims: list[Claim] = []
    for i, m in enumerate(marks):
        number = int(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end].strip()
        depends_on = _dependencies(body)
        claims.append(
            Claim(
                number=number,
                text=body,
                kind="dependent" if depends_on else "independent",
                depends_on=depends_on,
            )
        )
    return claims


def _dependencies(body: str) -> list[int]:
    """Numbers of claims this claim depends on (e.g. 'The device of claim 1' -> [1])."""
    nums: list[int] = []
    for m in _DEP_REF.finditer(body):
        for n in _DEP_NUM.findall(m.group(0)):
            v = int(n)
            if v not in nums:
                nums.append(v)
    return nums


# ── element detection (token-walk) ───────────────────────────────────────────────────────────

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
_QUANT_OF = {"plurality", "set", "series", "group", "number"}  # "a <X> of ..."

# Words that terminate a noun phrase after an article.
_STOP = {
    "of", "to", "for", "with", "and", "or", "that", "which", "wherein", "whereby", "where",
    "comprising", "comprises", "comprise", "including", "includes", "include", "having", "has",
    "have", "consisting", "configured", "adapted", "operable", "capable", "coupled", "connected",
    "attached", "disposed", "positioned", "mounted", "arranged", "being", "is", "are", "from",
    "in", "on", "at", "as", "when", "such", "so", "then", "said", "the", "a", "an", "based",
    "responsive", "according", "further", "whereas", "between", "into", "onto", "via", "through",
    "over", "under", "within", "per", "about", "above", "below", "along", "against", "upon",
    "whether", "each", "any", "one",
    # common claim verbs — a definite reference ends at the verb ("the core SHARES a cache").
    # Safe: the NP walker always keeps the first token, so element heads like "a display" survive.
    "share", "shares", "receive", "receives", "transmit", "transmits", "send", "sends", "store",
    "stores", "provide", "provides", "generate", "generates", "define", "defines", "form", "forms",
    "extend", "extends", "engage", "engages", "contact", "contacts", "connect", "connects", "couple",
    "couples", "hold", "holds", "support", "supports", "move", "moves", "cause", "causes", "enable",
    "enables", "allow", "allows", "permit", "permits", "cover", "covers", "surround", "surrounds",
    "indicate", "indicates", "output", "outputs", "produce", "produces", "determine", "determines",
    "compute", "computes", "select", "selects", "control", "controls", "actuate", "actuates",
    "rotate", "rotates", "display", "displays", "perform", "performs", "process", "processes",
    "emit", "emits", "detect", "detects", "measure", "measures", "apply", "applies", "convert",
    "converts", "drive", "drives", "operate", "operates", "communicate", "communicates",
    "show", "shows", "contain", "contains", "represent", "represents", "correspond", "corresponds",
    "depend", "depends", "relate", "relates", "identify", "identifies", "record", "records",
    "return", "returns", "retrieve", "retrieves", "obtain", "obtains", "compare", "compares",
}
# -ing / -ed nouns that can legitimately be an element head (not treated as participles).
_NOUN_ING_ED = {
    "housing", "casing", "coating", "bearing", "opening", "wiring", "coupling", "spring", "ring",
    "string", "ceiling", "tubing", "padding", "cladding", "winding", "siding", "heading", "bushing",
    "printed", "feed", "seed", "shield", "weld", "thread", "lead", "electrode",
}
# Definite phrases (by head/first token) that are patent boilerplate and need no antecedent.
_BOILERPLATE = {
    "group", "art", "invention", "same", "like", "number", "case", "following", "drawings",
    "figures", "specification", "embodiment", "embodiments", "ones", "plurality", "claimed",
    "accompanying", "appended", "present", "prior",
}


def _is_participle(w: str) -> bool:
    return (w.endswith("ing") or w.endswith("ed")) and w not in _NOUN_ING_ED


def _singular(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ss") or w.endswith("us") or w.endswith("is"):
        return w  # apparatus, status, axis... already singular
    if w.endswith("s") and len(w) > 3:
        return w[:-1]
    return w


def _walk_np(words: list[str], j: int) -> list[str]:
    """Noun-phrase head starting at word index j: keep the first word, then take words up to a
    stop word or a participle. Capped at 5 words."""
    out: list[str] = []
    for k in range(j, min(j + 5, len(words))):
        w = words[k].lower()
        if k > j and (w in _STOP or _is_participle(w)):
            break
        out.append(w.lower())
    return out


def _elements(body: str) -> tuple[list[tuple[int, list[str]]], list[tuple[int, list[str], str]]]:
    """Return (introductions, references).
    introductions: (position, np-tokens) for 'a/an/at least one/a plurality of ... X'.
    references:    (position, np-tokens, article) for 'the/said X'."""
    toks = [(m.group(0), m.start()) for m in _WORD.finditer(body)]
    words = [t[0] for t in toks]
    intros: list[tuple[int, list[str]]] = []
    refs: list[tuple[int, list[str], str]] = []
    i, n = 0, len(toks)
    while i < n:
        w, pos = words[i].lower(), toks[i][1]
        if w in ("a", "an"):
            # "a plurality of X" / "a set of X" ...
            if w == "a" and i + 2 < n and words[i + 1].lower() in _QUANT_OF and words[i + 2].lower() == "of":
                np = _walk_np(words, i + 3)
                if np:
                    intros.append((pos, np))
                i += 3
                continue
            np = _walk_np(words, i + 1)
            if np:
                intros.append((pos, np))
            i += 1
            continue
        if w == "at" and i + 2 < n and words[i + 1].lower() == "least" and words[i + 2].lower() == "one":
            np = _walk_np(words, i + 3)
            if np:
                intros.append((pos, np))
            i += 3
            continue
        if w == "one" and i + 2 < n and words[i + 1].lower() == "or" and words[i + 2].lower() == "more":
            np = _walk_np(words, i + 3)
            if np:
                intros.append((pos, np))
            i += 3
            continue
        if w in ("the", "said"):
            np = _walk_np(words, i + 1)
            if np:
                refs.append((pos, np, words[i]))
            i += 1
            continue
        i += 1
    return intros, refs


def _matches(ref: list[str], intro: list[str]) -> bool:
    """Is a definite reference covered by an introduced element? The element sits at the HEAD of the
    phrase (right after the article); anything after it (a trailing verb the walker over-captured) is
    noise. So they match if the shorter token list is a prefix OR a suffix of the longer (singularised):
      • 'second core'  vs 'second core share'   -> intro is a prefix of ref  ✓ (trailing verb)
      • 'assembly'     vs 'widget assembly'     -> ref is a suffix of intro   ✓ (shortened reference)
      • 'first core'   vs 'second core'         -> neither                    ✗ (genuinely different)
    """
    if not ref or not intro:
        return False
    a = [_singular(w) for w in ref]
    b = [_singular(w) for w in intro]
    if a == b:
        return True
    short, long = (a, b) if len(a) < len(b) else (b, a)
    n = len(short)
    return short == long[:n] or short == long[-n:]


def _check_antecedent_basis(claim: Claim, by_number: dict[int, Claim]) -> list[Finding]:
    # elements introduced anywhere in the dependency chain (position irrelevant for ancestors)
    ancestor_intros: list[list[str]] = []
    seen: set[int] = set()
    stack = list(claim.depends_on)
    while stack:
        num = stack.pop()
        if num in seen or num not in by_number:
            continue
        seen.add(num)
        parent = by_number[num]
        ancestor_intros += [np for _, np in _elements(parent.text)[0]]
        stack += parent.depends_on

    own_intros, refs = _elements(claim.text)
    findings: list[Finding] = []
    for pos, phrase, article in refs:
        if phrase[-1] in _BOILERPLATE or phrase[0] in _BOILERPLATE:
            continue
        covered = any(_matches(phrase, a) for a in ancestor_intros) or any(
            ip < pos and _matches(phrase, inp) for ip, inp in own_intros
        )
        if not covered:
            display = " ".join(phrase)
            span = f"{article} {display}"
            findings.append(
                Finding(
                    claim_number=claim.number,
                    kind="antecedent_basis",
                    severity="error",
                    element=display,
                    span=span,
                    message=f"'{span}' lacks antecedent basis — the element '{display}' is never "
                    f"introduced with 'a'/'an' in claim {claim.number} or the claims it depends on.",
                )
            )
    return findings


# ── other structural checks ────────────────────────────────────────────────────────────────

_ABBREV = re.compile(r"\b(?:e\.g|i\.e|etc|vs|no|fig|figs|u\.s|et al)\.$", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"\.\s+(?=[A-Z])")


def _check_single_sentence(claim: Claim) -> list[Finding]:
    body = claim.text.rstrip()
    body = body[:-1] if body.endswith(".") else body  # drop the single terminal period
    real = [p for p in _SENTENCE_SPLIT.split(body) if p.strip()]
    if len(real) <= 1 or _ABBREV.search(real[0] + "."):
        return []
    return [
        Finding(
            claim_number=claim.number,
            kind="single_sentence",
            severity="error",
            element=None,
            span=(real[0][-40:] + ". " + real[1][:40]).strip(),
            message=f"Claim {claim.number} appears to be written as more than one sentence; "
            f"a claim must be a single sentence.",
        )
    ]


def _check_dependency(claim: Claim, numbers: set[int]) -> list[Finding]:
    findings: list[Finding] = []
    for r in claim.depends_on:
        if r == claim.number:
            msg, el = f"Claim {claim.number} depends on itself.", "self-reference"
        elif r > claim.number:
            msg, el = (
                f"Claim {claim.number} depends on claim {r}, which appears later — a claim may only "
                f"depend on a preceding claim.",
                f"claim {r}",
            )
        elif r not in numbers:
            msg, el = f"Claim {claim.number} depends on claim {r}, which does not exist.", f"claim {r}"
        else:
            continue
        findings.append(
            Finding(
                claim_number=claim.number,
                kind="dependency",
                severity="error",
                element=el,
                span=f"claim {r}",
                message=msg,
            )
        )
    return findings


_RELATIVE_TERMS = [
    "substantially", "approximately", "about", "relatively", "sufficiently", "essentially",
    "generally", "preferably", "optionally", "roughly", "nearly", "almost", "somewhat",
    "optimal", "superior", "effective amount",
]


def _check_indefiniteness(claim: Claim) -> list[Finding]:
    findings: list[Finding] = []
    low = claim.text.lower()
    for term in _RELATIVE_TERMS:
        m = re.search(rf"\b{re.escape(term)}\b", low)
        if not m:
            continue
        start = max(0, m.start() - 15)
        span = claim.text[start : m.end() + 15].strip()
        findings.append(
            Finding(
                claim_number=claim.number,
                kind="indefiniteness",
                severity="advisory",
                element=term,
                span=span,
                message=f"Relative term of degree '{term}' in claim {claim.number} may draw a "
                f"§112(b) indefiniteness objection unless the specification bounds it.",
            )
        )
    return findings


def check(claims: list[Claim]) -> list[Finding]:
    """Run every deterministic check over a parsed claim set. Findings, in claim order."""
    by_number = {c.number: c for c in claims}
    numbers = set(by_number)
    findings: list[Finding] = []
    for claim in claims:
        dep_findings = _check_dependency(claim, numbers)
        findings += dep_findings
        findings += _check_single_sentence(claim)
        # A claim whose dependency is broken has no valid antecedent chain — checking its definite
        # references would just cascade noise, so skip antecedent basis for it.
        if not dep_findings:
            findings += _check_antecedent_basis(claim, by_number)
        findings += _check_indefiniteness(claim)
    return findings


def analyze(text: str) -> tuple[list[Claim], list[Finding]]:
    """Parse + check, deterministically. No LLM."""
    claims = parse_claims(text)
    return claims, check(claims)
