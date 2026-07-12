"""Structural field-presence audit for materialized EDINET claims.

Scores three claim families against fixed expected-field schemas:

  * PolicyShareholding    (investor, issuer, share_count, carrying_amount,
                           holding_purpose, reciprocal_holding_marker,
                           evidence_element, information_status,
                           normative_status, evidence_locator,
                           reporting_period_validity)
  * MajorShareholderClaim (issuer, holder, holder_role, share_count,
                           ownership_percentage, shareholder_rank,
                           evidence_element, information_status,
                           normative_status, evidence_locator,
                           reporting_period_validity)
  * CrossShareholdingClaim (investor, issuer, dual_evidence_traceability,
                            jcn_identity_resolution, information_status,
                            evidence_locator, reporting_period_validity)

The "vanilla" sets below are author-defined comparison subsets. The audit does
not execute vanilla FIBO, compare extracted values with filing ground truth, or
measure correctness. It reports which expected predicates are present in the
materialized J-FIBO claim graph.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, PROV, RDF, SKOS, XSD

REPO = Path(__file__).resolve().parents[1]
CLAIMS_DIR = REPO / "data" / "edinet" / "claims"
RESULTS_DIR = REPO / "benchmark" / "results"

JPFIBO = Namespace("https://w3id.org/jfibo/ontology/JP/core/")

POLICY_EXPECTED = [
    "investor", "issuer", "share_count", "carrying_amount", "holding_purpose",
    "reciprocal_holding_marker", "evidence_element", "information_status",
    "normative_status", "evidence_locator", "reporting_period_validity",
]
POLICY_VANILLA = {"investor", "issuer", "share_count"}

MAJOR_EXPECTED = [
    "issuer", "holder", "holder_role", "share_count", "ownership_percentage",
    "shareholder_rank", "evidence_element", "information_status",
    "normative_status", "evidence_locator", "reporting_period_validity",
]
MAJOR_VANILLA = {"issuer", "holder", "share_count", "ownership_percentage"}

CROSS_EXPECTED = [
    "investor", "issuer", "dual_evidence_traceability",
    "jcn_identity_resolution", "information_status", "evidence_locator",
    "reporting_period_validity",
]
CROSS_VANILLA = {"investor", "issuer"}

BORROWINGS_EXPECTED = [
    "borrower", "borrowings_class_label", "opening_balance",
    "closing_balance", "average_rate", "repayment_deadline",
    "unit_label", "evidence_element", "information_status",
    "normative_status", "evidence_locator", "reporting_period_validity",
]
BORROWINGS_VANILLA = {"borrower"}

COMMERCIAL_PAPER_EXPECTED = [
    "borrower", "borrowings_class_label", "opening_balance",
    "closing_balance", "average_rate", "unit_label",
    "evidence_element", "information_status", "normative_status",
    "evidence_locator", "reporting_period_validity",
]
COMMERCIAL_PAPER_VANILLA = {"borrower"}

EXPECTED_BY_KIND = {
    "PolicyShareholding": POLICY_EXPECTED,
    "MajorShareholderClaim": MAJOR_EXPECTED,
    "CrossShareholdingClaim": CROSS_EXPECTED,
    "BorrowingsClaim": BORROWINGS_EXPECTED,
    "CommercialPaperClaim": COMMERCIAL_PAPER_EXPECTED,
}


def _ratio(a: int, b: int) -> float:
    return float(a) / float(b) if b else 0.0


def _has_jcn_identity(g: Graph, entity: URIRef | None) -> bool:
    if not isinstance(entity, URIRef):
        return False
    if "/entity/jcn/" in str(entity):
        return True
    equivalents = set(g.objects(entity, OWL.sameAs))
    equivalents.update(g.subjects(OWL.sameAs, entity))
    return any(
        isinstance(candidate, URIRef) and "/entity/jcn/" in str(candidate)
        for candidate in equivalents
    )


def policy_metrics(g: Graph) -> list[dict]:
    out: list[dict] = []
    for c in g.subjects(RDF.type, JPFIBO.PolicyShareholding):
        f: set[str] = set()
        if g.value(c, JPFIBO.hasInvestor): f.add("investor")
        if g.value(c, JPFIBO.hasIssuer): f.add("issuer")
        if g.value(c, JPFIBO.hasShareCount) is not None: f.add("share_count")
        if g.value(c, JPFIBO.hasCarryingAmount) is not None: f.add("carrying_amount")
        if g.value(c, JPFIBO.hasHoldingPurpose): f.add("holding_purpose")
        if any(g.objects(c, SKOS.note)): f.add("reciprocal_holding_marker")
        if any(g.objects(c, JPFIBO.hasEvidenceElement)): f.add("evidence_element")
        if g.value(c, JPFIBO.informationStatus): f.add("information_status")
        if g.value(c, JPFIBO.normativeStatus): f.add("normative_status")
        if g.value(c, PROV.wasDerivedFrom): f.add("evidence_locator")
        if g.value(c, DCTERMS.valid): f.add("reporting_period_validity")
        v = f & POLICY_VANILLA
        out.append({
            "claim": str(c), "kind": "PolicyShareholding",
            "fields": sorted(f),
            "vanilla_coverage": _ratio(len(v), len(POLICY_EXPECTED)),
            "jfibo_coverage":   _ratio(len(f), len(POLICY_EXPECTED)),
        })
    return out


def major_metrics(g: Graph) -> list[dict]:
    out: list[dict] = []
    for c in g.subjects(RDF.type, JPFIBO.MajorShareholderClaim):
        f: set[str] = set()
        if g.value(c, JPFIBO.hasIssuer): f.add("issuer")
        if g.value(c, JPFIBO.hasHolder): f.add("holder")
        if g.value(c, JPFIBO.holderRole): f.add("holder_role")
        if g.value(c, JPFIBO.hasShareCount) is not None: f.add("share_count")
        if g.value(c, JPFIBO.hasOwnershipPercentage) is not None: f.add("ownership_percentage")
        if g.value(c, JPFIBO.hasShareholderRank) is not None: f.add("shareholder_rank")
        if any(g.objects(c, JPFIBO.hasEvidenceElement)): f.add("evidence_element")
        if g.value(c, JPFIBO.informationStatus): f.add("information_status")
        if g.value(c, JPFIBO.normativeStatus): f.add("normative_status")
        if g.value(c, PROV.wasDerivedFrom): f.add("evidence_locator")
        if g.value(c, DCTERMS.valid): f.add("reporting_period_validity")
        v = f & MAJOR_VANILLA
        out.append({
            "claim": str(c), "kind": "MajorShareholderClaim",
            "fields": sorted(f),
            "vanilla_coverage": _ratio(len(v), len(MAJOR_EXPECTED)),
            "jfibo_coverage":   _ratio(len(f), len(MAJOR_EXPECTED)),
        })
    return out


def cross_metrics(g: Graph) -> list[dict]:
    out: list[dict] = []
    for c in g.subjects(RDF.type, JPFIBO.CrossShareholdingClaim):
        f: set[str] = set()
        investor = g.value(c, JPFIBO.hasInvestor)
        issuer = g.value(c, JPFIBO.hasIssuer)
        if investor: f.add("investor")
        if issuer: f.add("issuer")
        derived = list(g.objects(c, PROV.wasDerivedFrom))
        if len(derived) >= 2: f.add("dual_evidence_traceability")
        if _has_jcn_identity(g, investor) and _has_jcn_identity(g, issuer):
            f.add("jcn_identity_resolution")
        if g.value(c, JPFIBO.informationStatus): f.add("information_status")
        if g.value(c, PROV.wasDerivedFrom): f.add("evidence_locator")
        if g.value(c, DCTERMS.valid): f.add("reporting_period_validity")
        v = f & CROSS_VANILLA
        out.append({
            "claim": str(c), "kind": "CrossShareholdingClaim",
            "fields": sorted(f),
            "vanilla_coverage": _ratio(len(v), len(CROSS_EXPECTED)),
            "jfibo_coverage":   _ratio(len(f), len(CROSS_EXPECTED)),
        })
    return out



def borrowings_metrics(g: Graph) -> list[dict]:
    out: list[dict] = []
    for c in g.subjects(RDF.type, JPFIBO.BorrowingsClaim):
        f: set[str] = set()
        if g.value(c, JPFIBO.hasBorrower): f.add("borrower")
        if g.value(c, JPFIBO.hasBorrowingsClassLabel): f.add("borrowings_class_label")
        if g.value(c, JPFIBO.hasOpeningBalance) is not None: f.add("opening_balance")
        if g.value(c, JPFIBO.hasClosingBalance) is not None: f.add("closing_balance")
        if g.value(c, JPFIBO.hasAverageRate) is not None: f.add("average_rate")
        if g.value(c, JPFIBO.hasRepaymentDeadline): f.add("repayment_deadline")
        if g.value(c, JPFIBO.hasUnitLabel): f.add("unit_label")
        if any(g.objects(c, JPFIBO.hasEvidenceElement)): f.add("evidence_element")
        if g.value(c, JPFIBO.informationStatus): f.add("information_status")
        if g.value(c, JPFIBO.normativeStatus): f.add("normative_status")
        if g.value(c, PROV.wasDerivedFrom): f.add("evidence_locator")
        if g.value(c, DCTERMS.valid): f.add("reporting_period_validity")
        v = f & BORROWINGS_VANILLA
        out.append({
            "claim": str(c), "kind": "BorrowingsClaim",
            "fields": sorted(f),
            "vanilla_coverage": _ratio(len(v), len(BORROWINGS_EXPECTED)),
            "jfibo_coverage":   _ratio(len(f), len(BORROWINGS_EXPECTED)),
        })
    return out


def commercial_paper_metrics(g: Graph) -> list[dict]:
    out: list[dict] = []
    for c in g.subjects(RDF.type, JPFIBO.CommercialPaperClaim):
        f: set[str] = set()
        if g.value(c, JPFIBO.hasBorrower): f.add("borrower")
        if g.value(c, JPFIBO.hasBorrowingsClassLabel): f.add("borrowings_class_label")
        if g.value(c, JPFIBO.hasOpeningBalance) is not None: f.add("opening_balance")
        if g.value(c, JPFIBO.hasClosingBalance) is not None: f.add("closing_balance")
        if g.value(c, JPFIBO.hasAverageRate) is not None: f.add("average_rate")
        if g.value(c, JPFIBO.hasUnitLabel): f.add("unit_label")
        if any(g.objects(c, JPFIBO.hasEvidenceElement)): f.add("evidence_element")
        if g.value(c, JPFIBO.informationStatus): f.add("information_status")
        if g.value(c, JPFIBO.normativeStatus): f.add("normative_status")
        if g.value(c, PROV.wasDerivedFrom): f.add("evidence_locator")
        if g.value(c, DCTERMS.valid): f.add("reporting_period_validity")
        v = f & COMMERCIAL_PAPER_VANILLA
        out.append({
            "claim": str(c), "kind": "CommercialPaperClaim",
            "fields": sorted(f),
            "vanilla_coverage": _ratio(len(v), len(COMMERCIAL_PAPER_EXPECTED)),
            "jfibo_coverage":   _ratio(len(f), len(COMMERCIAL_PAPER_EXPECTED)),
        })
    return out

def run(claims_dir: Path = CLAIMS_DIR) -> dict:
    per_doc: dict[str, list[dict]] = {}
    all_claims: list[dict] = []
    for p in sorted(claims_dir.glob("*.ttl")):
        g = Graph().parse(p)
        m = (policy_metrics(g) + major_metrics(g) + cross_metrics(g) + borrowings_metrics(g) + commercial_paper_metrics(g))
        per_doc[p.stem] = m
        for x in m:
            x["doc_id"] = p.stem
        all_claims.extend(m)

    if not all_claims:
        return {"claims": 0}

    by_kind = defaultdict(list)
    for c in all_claims:
        by_kind[c["kind"]].append(c)

    summary = {
        "methodology": {
            "kind": "materialized_claim_field_presence",
            "independent_ground_truth": False,
            "vanilla_baseline": "author_defined_field_subset",
            "not_valid_for": "proving extraction accuracy or ontology superiority",
        },
        "claims": len(all_claims),
        "mean_vanilla_coverage": statistics.fmean(c["vanilla_coverage"] for c in all_claims),
        "mean_jfibo_coverage":   statistics.fmean(c["jfibo_coverage"]   for c in all_claims),
        "mean_jfibo_gain":       statistics.fmean(c["jfibo_coverage"] - c["vanilla_coverage"] for c in all_claims),
        "by_kind": {},
    }
    for kind, claims in sorted(by_kind.items()):
        expected = EXPECTED_BY_KIND[kind]
        field_presence = {
            field: {
                "present": sum(field in claim["fields"] for claim in claims),
                "missing": sum(field not in claim["fields"] for claim in claims),
                "rate": _ratio(
                    sum(field in claim["fields"] for claim in claims),
                    len(claims),
                ),
            }
            for field in expected
        }
        summary["by_kind"][kind] = {
            "claims": len(claims),
            "complete_claims": sum(
                len(claim["fields"]) == len(expected) for claim in claims
            ),
            "mean_vanilla_coverage": statistics.fmean(
                claim["vanilla_coverage"] for claim in claims
            ),
            "mean_jfibo_coverage": statistics.fmean(
                claim["jfibo_coverage"] for claim in claims
            ),
            "mean_jfibo_gain": statistics.fmean(
                claim["jfibo_coverage"] - claim["vanilla_coverage"]
                for claim in claims
            ),
            "field_presence": field_presence,
        }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims-dir", type=Path, default=CLAIMS_DIR)
    ap.add_argument("--out", type=Path, default=RESULTS_DIR / "real_summary.json")
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary = run(args.claims_dir)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary or summary.get("claims", 0) == 0:
        print("no claims found"); return 0
    print("J-FIBO materialized-claim field-presence audit")
    print("=" * 52)
    print(f"claims:                          {summary['claims']}")
    print(f"mean declared vanilla subset:    {summary['mean_vanilla_coverage']:.3f}")
    print(f"mean J-FIBO field presence:      {summary['mean_jfibo_coverage']:.3f}")
    print(f"mean declared-field difference:  {summary['mean_jfibo_gain']:.3f}")
    print()
    print("by claim kind:")
    for k, v in summary["by_kind"].items():
        print(
            f"  {k:24s} claims={v['claims']:>3}  "
            f"complete={v['complete_claims']:>3}  "
            f"vanilla={v['mean_vanilla_coverage']:.3f}  "
            f"jfibo={v['mean_jfibo_coverage']:.3f}  "
            f"gain={v['mean_jfibo_gain']:.3f}"
        )
        missing = [
            f"{field}:{stats['missing']}"
            for field, stats in v["field_presence"].items()
            if stats["missing"]
        ]
        if missing:
            print(f"    missing fields: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
