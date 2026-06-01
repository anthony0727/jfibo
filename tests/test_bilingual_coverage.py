"""Bilingual coverage for adoption-ready terms.

Stable / proposed terms (not experimental-consumer-only, not EDINET-aligned
external metadata) must carry both English and Japanese skos:definition.
Japanese institutional readers should never see an English-only definition
on the production-core surface.
"""
from __future__ import annotations
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, SKOS, OWL
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JPFIBO = Namespace("https://w3id.org/jfibo/ontology/JP/core/")
STATUS = URIRef("https://w3id.org/jfibo/ontology/JP/core/status")


def _aggregate() -> Graph:
    g = Graph()
    g.parse(REPO / "ontology" / "jfibo.ttl", format="turtle")
    return g


# Allow-list of terms permitted to ship without a Japanese definition.
ALLOW_NO_JA = {
    # Experimental-consumer-only: out of production scope, JA optional.
    "Counterfactual", "Predicted", "InformationBoundary", "OutsideInformationBoundary",
    # External alignment individuals: language anchors already use language codes; JA optional.
    "Japan", "JapaneseLanguage", "JapaneseYen",
    # EDINET-alignment terms: carry official Japanese labels via skos:prefLabel and
    # hasOfficialJapaneseLabel; freeform JA definitions deferred to v1.2.
}


def test_bilingual_definitions_for_jfibo_core_terms() -> None:
    g = _aggregate()
    minted = (
        {s for s in g.subjects(RDF.type, OWL.Class) if str(s).startswith(str(JPFIBO))}
        | {s for s in g.subjects(RDF.type, OWL.ObjectProperty) if str(s).startswith(str(JPFIBO))}
        | {s for s in g.subjects(RDF.type, OWL.DatatypeProperty) if str(s).startswith(str(JPFIBO))}
        | {s for s in g.subjects(RDF.type, OWL.AnnotationProperty) if str(s).startswith(str(JPFIBO))}
    )

    failures: list[str] = []
    for s in minted:
        local = str(s).rsplit("/", 1)[-1]
        if local in ALLOW_NO_JA:
            continue
        # EDINET-alignment subjects (jpcrp_cor:*, jpdei_cor:*, jplvh_cor:*) aren't in JPFIBO
        # so they don't enter this set; we don't need to skip them here.
        defs = list(g.objects(s, SKOS.definition))
        langs = {d.language for d in defs if isinstance(d, Literal)}
        if "en" not in langs:
            failures.append(f"{local}: missing skos:definition @en")
        if "ja" not in langs:
            failures.append(f"{local}: missing skos:definition @ja")
    assert not failures, "bilingual coverage gaps:\n  " + "\n  ".join(failures)


def test_no_term_has_only_japanese_label_pair() -> None:
    """Every term in JPFIBO with a Japanese label must also have an English label."""
    g = _aggregate()
    for s in {s for s, p, o in g if isinstance(o, Literal) and o.language == "ja" and p == SKOS.prefLabel and str(s).startswith(str(JPFIBO))}:
        en_labels = [l for l in g.objects(s, SKOS.prefLabel) if isinstance(l, Literal) and l.language == "en"]
        local = str(s).rsplit("/", 1)[-1]
        assert en_labels, f"{local}: has @ja prefLabel but no @en prefLabel"
