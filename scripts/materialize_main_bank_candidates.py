"""Materialize jfibo:MainBankCandidate claims from major-shareholder evidence.

Rule (v1.1, narrow on purpose):
  Issue a MainBankCandidate(issuer=X, candidate=Y) iff
    1. Y appears as a holder of X in X's major-shareholders table, AND
    2. Y's name matches a Japanese commercial-bank or financial-group pattern
       (㈱X銀行, X信託銀行, XFG, ㈱Xフィナンシャルグループ), AND
    3. Y's holder_role is RegisteredHolder (NOT Trustee, NOT CustodyBank —
       trust banks / custodians appearing in the table are not the main bank).

  We cite at least 2 distinct evidence items per claim, as required by
  jfibo:MainBankCandidateShape:
    - the major-shareholder row (as an EvidenceItem)
    - the parent EDINETDisclosureDocument

  informationStatus is fixed to jfibo:Hypothesized: this is candidacy from
  a single class of evidence (equity holding), not a confirmed main-bank
  relationship. A v2 materializer would also intersect with the borrowings
  schedule when both are parsed.

Output is appended into existing per-filing claim TTLs in
data/edinet/claims/<docID>.ttl so the rest of the pipeline (count_coverage,
real_data_loss benchmark) picks them up automatically.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import hashlib
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF, RDFS, SKOS, XSD

REPO = Path(__file__).resolve().parents[1]
MS_DIR = REPO / "data" / "edinet" / "major_shareholders"
CLAIMS_DIR = REPO / "data" / "edinet" / "claims"

JPFIBO = Namespace("https://w3id.org/jfibo/ontology/JP/core/")
EVIDENCE = Namespace("https://w3id.org/jfibo/evidence/")
CLAIM = Namespace("https://w3id.org/jfibo/claim/")
ENTITY = Namespace("https://w3id.org/jfibo/entity/")

# Names of commercial banks and bank holding companies whose direct equity
# holding (as RegisteredHolder) signals a main-bank candidacy. Conservative
# list — extending requires source review.
BANK_NAME_PATTERNS = [
    re.compile(r"㈱?\s*三菱ＵＦＪ銀行"),
    re.compile(r"㈱?\s*みずほ銀行"),
    re.compile(r"㈱?\s*三井住友銀行"),
    re.compile(r"株式会社三菱ＵＦＪ銀行"),
    re.compile(r"株式会社みずほ銀行"),
    re.compile(r"株式会社三井住友銀行"),
    re.compile(r"りそな銀行"),
    re.compile(r"三井住友信託銀行"),
    re.compile(r"三菱ＵＦＪ信託銀行"),
    re.compile(r"みずほ信託銀行"),
    re.compile(r"㈱?\s*三菱ＵＦＪフィナンシャル・グループ"),
    re.compile(r"㈱?\s*みずほフィナンシャルグループ"),
    re.compile(r"㈱?\s*三井住友フィナンシャルグループ"),
]


def looks_like_bank(name: str) -> bool:
    if not name:
        return False
    return any(p.search(name) for p in BANK_NAME_PATTERNS)


def short_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def materialize(filing_path: Path) -> int:
    """Append MainBankCandidate triples to claims/<docID>.ttl. Return count emitted."""
    d = json.loads(filing_path.read_text())
    doc_id = d.get("doc_id") or filing_path.stem
    issuer_name = d.get("filer_name_ja", "")
    issuer_iri_raw = d.get("filer_iri") or f"urn:jfibo:issuer-fallback:{short_id(issuer_name)}"
    issuer_iri = URIRef(issuer_iri_raw)

    rows = d.get("rows", [])
    candidates = []
    for r in rows:
        name = (r.get("name") or "").strip()
        role = r.get("holder_role")
        if role not in ("RegisteredHolder",):
            continue
        if not looks_like_bank(name):
            continue
        candidates.append(r)

    if not candidates:
        return 0

    g = Graph()
    g.bind("jfibo", JPFIBO)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    g.bind("skos", SKOS)

    doc_iri = URIRef(f"https://w3id.org/jfibo/document/edinet/{doc_id}")
    g.add((doc_iri, RDF.type, JPFIBO.EDINETDisclosureDocument))

    for r in candidates:
        bank_name = r.get("name", "").strip()
        bank_iri = URIRef(f"{ENTITY}name/{short_id(bank_name)}")
        g.add((bank_iri, RDFS.label, Literal(bank_name, lang="ja")))

        claim_iri = URIRef(
            f"{CLAIM}main-bank-candidate/{doc_id}/{short_id(bank_name + issuer_name)}"
        )
        g.add((claim_iri, RDF.type, JPFIBO.MainBankCandidate))
        g.add((claim_iri, JPFIBO.hasIssuer, issuer_iri))
        g.add((claim_iri, JPFIBO.hasLender, bank_iri))
        g.add((claim_iri, JPFIBO.informationStatus, JPFIBO.Hypothesized))
        g.add((claim_iri, JPFIBO.normativeStatus, JPFIBO.InstitutionalExpectation))
        g.add((claim_iri, JPFIBO.reportingRegime, JPFIBO.FinancialInstrumentsAndExchangeAct))
        # Validity = the period end of the disclosure. Pulled from the filing metadata
        # when present, with a sensible default for FY2024 reports (2025-03-31).
        period_end = d.get("period_end") or "2025-03-31"
        g.add((claim_iri, DCTERMS.valid, Literal(period_end, datatype=XSD.date)))
        # prov:generatedAtTime — when this claim was emitted by the materializer.
        import datetime as _dt
        g.add((claim_iri, PROV.generatedAtTime,
               Literal(_dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat(), datatype=XSD.dateTime)))
        g.add((claim_iri, RDFS.comment, Literal(
            f"Hypothesized main-bank candidacy: {bank_name} appears as a "
            f"RegisteredHolder of {issuer_name} (rank {r.get('rank')}, "
            f"{r.get('ownership_pct')}%) in the FY annual securities report. "
            f"Direct equity holding by a commercial bank or bank holding company "
            f"is a Japanese keiretsu main-bank signal, but candidacy is not "
            f"confirmation; corroborate with borrowings schedule.",
            lang="en",
        )))

        # Evidence items (>=2 required by shape)
        ev_row = URIRef(
            f"{EVIDENCE}major-shareholder-row/{doc_id}/rank-{r.get('rank')}"
        )
        g.add((ev_row, RDF.type, JPFIBO.EvidenceItem))
        g.add((ev_row, DCTERMS.source, URIRef(f"https://disclosure2.edinet-fsa.go.jp/api/v2/documents/{doc_id}")))
        g.add((ev_row, RDFS.label, Literal(
            f"major-shareholders row rank {r.get('rank')}, holder {bank_name}, "
            f"{r.get('ownership_pct')}%", lang="en")))

        ev_doc = URIRef(f"{EVIDENCE}edinet-document/{doc_id}")
        g.add((ev_doc, RDF.type, JPFIBO.EvidenceItem))
        g.add((ev_doc, DCTERMS.source, URIRef(f"https://disclosure2.edinet-fsa.go.jp/api/v2/documents/{doc_id}")))
        g.add((ev_doc, RDFS.label, Literal(
            f"EDINET disclosure document {doc_id} ({issuer_name})", lang="en")))

        g.add((claim_iri, PROV.wasDerivedFrom, ev_row))
        g.add((claim_iri, PROV.wasDerivedFrom, ev_doc))

    # Append to existing per-filing TTL.
    # IMPORTANT: original files were generated without rdfs:; we MUST add the
    # rdfs: prefix declaration before appending or the file will not parse.
    out = CLAIMS_DIR / f"{doc_id}.ttl"
    serialized = g.serialize(format="turtle")
    body_lines = [ln for ln in serialized.split("\n") if not ln.startswith("@prefix") and not ln.startswith("@base")]
    body = "\n".join(body_lines).strip()
    if out.exists():
        existing = out.read_text()
        if "# MainBankCandidate (v1.1)" in existing:
            return len(candidates)
        # Ensure rdfs: prefix is bound in the file (originals were missing it).
        if "@prefix rdfs:" not in existing:
            # Inject after the last @prefix line.
            lines = existing.split("\n")
            last_prefix = max(i for i, ln in enumerate(lines) if ln.startswith("@prefix"))
            lines.insert(last_prefix + 1, "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
            existing = "\n".join(lines)
            out.write_text(existing)
        with out.open("a") as f:
            f.write(f"\n\n# MainBankCandidate (v1.1)\n{body}\n")
    else:
        out.write_text(serialized)
    return len(candidates)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ms-dir", type=Path, default=MS_DIR)
    args = ap.parse_args()

    total = 0
    for p in sorted(args.ms_dir.glob("*.json")):
        n = materialize(p)
        print(f"{p.stem}: {n} MainBankCandidate(s)")
        total += n
    print(f"\ntotal: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
