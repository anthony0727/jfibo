"""Honda regression: the v0.5 corpus had Honda E02165 (wrong code, no filings found).
The actual code is E02166; v1.1.1 fixed it. This test prevents the typo class.

Verifies:
  1. The Honda EDINET code is E02166 in scripts/find_target_filings.py
  2. Honda's FY2024 securities report (docID S100VYOD) is in the raw corpus
  3. Honda has materialized claims (PolicyShareholding and MajorShareholderClaim)
"""
from __future__ import annotations
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_honda_edinet_code_is_correct() -> None:
    src = (REPO / "scripts" / "find_target_filings.py").read_text()
    m = re.search(r'"Honda Motor Co\., Ltd\."\s*:\s*"(E\d+)"', src)
    assert m, "Honda target entry not found"
    assert m.group(1) == "E02166", (
        f"Honda EDINET code must be E02166 (本田技研工業株式会社), "
        f"not {m.group(1)} (v0.5 typo)"
    )


def test_honda_securities_report_is_in_corpus() -> None:
    assert (REPO / "data" / "edinet" / "raw" / "S100VYOD.xbrl.zip").exists(), (
        "Honda FY2024 securities report (S100VYOD) missing from data/edinet/raw/"
    )


def test_honda_has_materialized_claims() -> None:
    ttl = REPO / "data" / "edinet" / "claims" / "S100VYOD.ttl"
    assert ttl.exists(), "Honda claims TTL missing"
    text = ttl.read_text()
    # Honda is a non-bank issuer with policy holdings + major shareholders.
    # We expect at least PolicyShareholding and MajorShareholderClaim classes
    # to appear; the exact counts can drift across re-materializations but
    # must remain non-zero.
    assert re.search(r"\ba +jfibo:PolicyShareholding\b", text), (
        "Honda should have at least one PolicyShareholding claim"
    )
    assert re.search(r"\ba +jfibo:MajorShareholderClaim\b", text), (
        "Honda should have at least one MajorShareholderClaim claim"
    )
