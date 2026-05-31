# Coverage (v1.0)

Honest scope. Two axes: **conceptual coverage** (does the ontology define the
right things at the right level of abstraction?) and **disclosure coverage**
(how much of the EDINET XBRL taxonomy is mapped, and how many filings have
been materialized as instance data?).

A production-grade ontology can be conceptually complete while disclosure-
coverage is partial. J-FIBO v1.0 targets the former; disclosure coverage
expands incrementally with each release.

## Conceptual coverage (the ontology core)

| Domain | v1.0 status |
|---|---|
| Legal forms (`KabushikiKaisha`, `GodoKaisha`, …) | stable |
| Reporting regimes (FIEL, Companies Act, Cabinet Office Ordinance, CG Code, JPX rules, TDnet) | stable |
| Disclosure document types (annual / quarterly / semi-annual / extraordinary securities reports, large-shareholding report, governance report, tender offer) | stable |
| Holder roles (beneficial, registered, trustee, nominee, custodian, strategic, pure-investment, policy) | stable |
| Ownership concepts (shareholding, policy shareholding, specified investment shares, cross-shareholding) | stable |
| Financing concepts (borrowings, syndicated loan, short/long-term, commercial paper) | stable |
| Institutional relationships (keiretsu, business alliance, capital alliance, parent-subsidiary, listed-subsidiary, stable-shareholder) | stable |
| Main-bank relationship | candidate-only (no production instances yet — see §Open work) |
| Information status (Observed, Disclosed, EvidenceBackedInferred, Hypothesized) | stable |
| Consumer-reasoning artifacts (Counterfactual, Predicted, InformationBoundary, OutsideInformationBoundary) | **experimental-consumer-only** — not part of production core; see `docs/term-status.md` |

## Disclosure coverage (EDINET XBRL taxonomy)

| Metric | Value |
|---:|:---|
| EDINET 2026 taxonomy elements (universe, all sheets of `1e_ElementList.xlsx`) | ~25,700 |
| Elements explicitly aligned in J-FIBO (`jfibo-edinet-alignment.ttl`) | 56 |
| Alignment coverage (by count) | ~0.22% |
| Alignment coverage (by *relevant-to-J-FIBO-domains*) | high on the elements that matter for v1.0 claim families; not yet measured per-domain |

J-FIBO does **not** attempt to map every EDINET element. The alignment is
scoped to the elements that materially support the claim families currently
modeled (policy shareholding, major shareholder, borrowings, commercial
paper, cross-shareholding). EDINET elements outside that scope (e.g.
segment-reporting detail rows, life-insurance-specific solvency lines) are
left to future modules.

If you need full EDINET coverage today, use the FSA's published taxonomy
directly; J-FIBO is the meaning layer on top of it, not a replacement.

## Filing materialization (instance data, not ontology)

Instance data is provided as reproducible examples, not as authoritative
content. The ontology stands on its own; the materialized claims are
illustrative.

| Filing | Issuer | Period | Status |
|---|---|---|---|
| `S100VWVY` | Toyota Motor Corporation | FY2024 (年度末 2025-03-31) | materialized |
| `S100VYN4` | ITOCHU Corporation (伊藤忠商事) | FY2024 | materialized |
| `S100W4FB` | Mitsubishi UFJ Financial Group | FY2024 | materialized |
| `S100W4HN` | SoftBank Group Corp. | FY2024 | materialized |
| Honda Motor Co., Ltd. (E02165) | — | FY2024 | **not yet materialized** — outside the current 400-day scan window; v0.5 dropped this silently. v1.0 surfaces the miss via `scripts/find_target_filings.py --strict`. See `tests/test_strict_targets.py`. |

### Claim families instantiated from those 4 filings

| Claim family | Count |
|---:|:---|
| `PolicyShareholding` | 176 |
| `MajorShareholderClaim` | 40 |
| `BorrowingsClaim` | 5 |
| `CommercialPaperClaim` | 1 |
| `CrossShareholdingClaim` | 1 (Toyota Motor ↔ MUFG, triangulated) |
| `MainBankCandidate` | 0 (see Open work) |
| **Total** | **223** |

## Known gaps and open work

1. **Honda Motor (E02165) FY2024 securities report** is not yet in the corpus.
   Root cause: the 400-day scan window starting at the v0.5 build time
   excluded Honda's submission date. v1.0 fixes the silent-drop behavior;
   re-running with a wider window will pick Honda up.
2. **`MainBankCandidate` has zero instances.** The concept is defined and
   shape-validated, but the materializer does not yet emit candidate edges
   from the borrowings schedule. This is the most visible Japan-specific
   gap and is the headline target for v1.1.
3. **No EDINET alignment for `LargeShareholdingReport` body elements.** Only
   the document-type concept itself is modeled. v1.1 should align the
   element-level fields once a filing of this type is in the corpus.
4. **No corpus from regional banks, life insurers, J-REITs, or trading-house
   subsidiaries.** Sector diversification is v1.1 work. The current four
   filings over-index on TSE Prime large-caps.
5. **EDINET alignment elements lack `dcterms:source` to the specific
   taxonomy version URL.** They reference the taxonomy generically;
   per-element URLs would be ideal. Tracked for v1.1.

## Reproducing the coverage numbers

```bash
uv run python scripts/count_coverage.py
```

This script (added in v1.0) walks `data/edinet/`, `data/derived/`, and
`ontology/`, and prints the table above against the current repo state. It
is invoked by CI so the README/coverage doc can never drift from reality
silently.
