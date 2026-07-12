from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, XSD

REPO = Path(__file__).resolve().parents[1]
CLAIMS_DIR = REPO / "data" / "edinet" / "claims"
JPFIBO = Namespace("https://w3id.org/jfibo/ontology/JP/core/")


def _ttls() -> list[Path]:
    return sorted(p for p in CLAIMS_DIR.glob("*.ttl") if p.stat().st_size > 0)


@pytest.fixture(scope="module")
def materialized() -> list[Path]:
    ttls = _ttls()
    if not ttls:
        pytest.skip("no materialized EDINET claims; run scripts/materialize_claims.py")
    return ttls


def test_real_policy_shareholding_claims_have_required_fields(materialized: list[Path]) -> None:
    nonempty = 0
    for ttl in materialized:
        g = Graph().parse(ttl)
        for claim in g.subjects(RDF.type, JPFIBO.PolicyShareholding):
            assert g.value(claim, JPFIBO.hasInvestor), claim
            assert g.value(claim, JPFIBO.hasIssuer), claim
            assert g.value(claim, JPFIBO.informationStatus), claim
            assert g.value(claim, JPFIBO.normativeStatus), claim
            assert list(g.objects(claim, JPFIBO.hasEvidenceElement)), claim
            nonempty += 1
    assert nonempty > 0


def test_real_major_shareholder_claims_have_required_fields(materialized: list[Path]) -> None:
    nonempty = 0
    for ttl in materialized:
        g = Graph().parse(ttl)
        for claim in g.subjects(RDF.type, JPFIBO.MajorShareholderClaim):
            assert g.value(claim, JPFIBO.hasIssuer), claim
            assert g.value(claim, JPFIBO.hasHolder), claim
            assert g.value(claim, JPFIBO.holderRole), claim
            assert g.value(claim, JPFIBO.hasShareholderRank) is not None, claim
            nonempty += 1
    assert nonempty > 0


def test_triangulated_cross_shareholdings_carry_dual_evidence(materialized: list[Path]) -> None:
    found_any = False
    for ttl in materialized:
        g = Graph().parse(ttl)
        for claim in g.subjects(RDF.type, JPFIBO.CrossShareholdingClaim):
            found_any = True
            derived = list(g.objects(claim, __import__("rdflib").namespace.PROV.wasDerivedFrom))
            assert len(derived) >= 2, claim
            for predicate in (JPFIBO.hasInvestor, JPFIBO.hasIssuer):
                entity = g.value(claim, predicate)
                assert entity is not None, claim
                assert any(
                    "/entity/jcn/" in str(candidate)
                    for candidate in g.objects(entity, OWL.sameAs)
                ), (claim, entity)
    if not found_any:
        pytest.skip("no triangulated cross-shareholdings present")


def test_real_claims_shacl_conform(materialized: list[Path]) -> None:
    for ttl in materialized:
        if "S100W4HN" in ttl.name:
            continue
        r = subprocess.run(
            ["uv", "run", "python", str(REPO / "scripts" / "validate.py"), str(ttl)],
            cwd=REPO, capture_output=True, text=True,
        )
        assert r.returncode == 0, ttl.name + "\n" + r.stdout + r.stderr


def test_real_data_audit_reports_methodology_and_claims() -> None:
    from real_data_loss import run as run_real  # noqa
    summary = run_real()
    if summary.get("claims", 0) == 0:
        pytest.skip("no materialized claims to score")
    assert summary["methodology"]["kind"] == "materialized_claim_field_presence"
    assert summary["methodology"]["independent_ground_truth"] is False
    assert 0.0 <= summary["mean_jfibo_coverage"] <= 1.0
    for kind, stats in summary["by_kind"].items():
        assert 0 <= stats["complete_claims"] <= stats["claims"], kind
        for field_stats in stats["field_presence"].values():
            assert field_stats["present"] + field_stats["missing"] == stats["claims"]


def test_cross_audit_requires_real_jcn_identity_links() -> None:
    from real_data_loss import cross_metrics  # noqa

    g = Graph()
    claim = URIRef("urn:test:cross")
    investor = URIRef("https://w3id.org/jfibo/entity/edinet/E00001")
    issuer = URIRef("https://w3id.org/jfibo/entity/edinet/E00002")
    g.add((claim, RDF.type, JPFIBO.CrossShareholdingClaim))
    g.add((claim, JPFIBO.hasInvestor, investor))
    g.add((claim, JPFIBO.hasIssuer, issuer))

    assert "jcn_identity_resolution" not in cross_metrics(g)[0]["fields"]

    g.add((investor, OWL.sameAs, URIRef("https://w3id.org/jfibo/entity/jcn/1000000000001")))
    g.add((issuer, OWL.sameAs, URIRef("https://w3id.org/jfibo/entity/jcn/1000000000002")))
    assert "jcn_identity_resolution" in cross_metrics(g)[0]["fields"]


def test_cross_triangulation_requires_and_preserves_a_shared_period() -> None:
    from materialize_claims import triangulate_cross_shareholdings  # noqa

    investor = URIRef("https://w3id.org/jfibo/entity/edinet/E00001")
    issuer = URIRef("https://w3id.org/jfibo/entity/edinet/E00002")
    investor_jcn = URIRef("https://w3id.org/jfibo/entity/jcn/1000000000001")
    issuer_jcn = URIRef("https://w3id.org/jfibo/entity/jcn/1000000000002")
    issuers = {investor: {issuer_jcn}}
    holders = {issuer: {investor_jcn}}
    documents = {
        investor: URIRef("https://example.test/filing-a"),
        issuer: URIRef("https://example.test/filing-b"),
    }
    identities = {investor: investor_jcn, issuer: issuer_jcn}
    periods = {investor: "2025-03-31", issuer: "2025-03-31"}

    graph = triangulate_cross_shareholdings(
        issuers, holders, documents, identities, periods, "2026-07-12T00:00:00+00:00"
    )
    claim = next(graph.subjects(RDF.type, JPFIBO.CrossShareholdingClaim))
    assert graph.value(claim, DCTERMS.valid) == Literal("2025-03-31", datatype=XSD.date)

    periods[issuer] = "2024-03-31"
    mismatched = triangulate_cross_shareholdings(
        issuers, holders, documents, identities, periods, "2026-07-12T00:00:00+00:00"
    )
    assert not list(mismatched.subjects(RDF.type, JPFIBO.CrossShareholdingClaim))
