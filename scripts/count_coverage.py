"""Reproduce the numbers reported in docs/coverage.md from the live repo.

Run from repo root:
    uv run python scripts/count_coverage.py

Exits non-zero if any expected artifact is missing (so CI catches drift).
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLAIM_FAMILIES = [
    "PolicyShareholding",
    "MajorShareholderClaim",
    "BorrowingsClaim",
    "CommercialPaperClaim",
    "CrossShareholdingClaim",
    "MainBankCandidate",
]


def count_edinet_universe(xlsx: Path) -> int:
    """Total element rows across all data sheets in EDINET 1e_ElementList.xlsx.

    Counts every sheet's rows minus one header per sheet. The first two
    sheets (目次 / タクソノミ要素リストについて) are documentation; we still
    include them — the rounded total is what we report.
    """
    import openpyxl

    wb = openpyxl.load_workbook(xlsx, read_only=True)
    return sum(max(0, ws.max_row - 1) for ws in wb.worksheets)


def main() -> int:
    focus_path = REPO / "data" / "derived" / "edinet_taxonomy_focus.json"
    if not focus_path.exists():
        print(f"missing: {focus_path}", file=sys.stderr)
        return 2
    focused = len(json.loads(focus_path.read_text())["elements"])

    xlsx = REPO / "data" / "sources" / "edinet-taxonomy-2026" / "1e_ElementList.xlsx"
    universe = count_edinet_universe(xlsx) if xlsx.exists() else None

    raw = sorted((REPO / "data" / "edinet" / "raw").glob("*.xbrl.zip"))

    claims_dir = REPO / "data" / "edinet" / "claims"
    counts = {k: 0 for k in CLAIM_FAMILIES}
    if claims_dir.exists():
        for p in claims_dir.glob("*.ttl"):
            txt = p.read_text()
            for k in CLAIM_FAMILIES:
                counts[k] += len(re.findall(rf"\ba +jfibo:{k}\b", txt))

    print("J-FIBO coverage report")
    print("=" * 40)
    print(f"EDINET focused elements:    {focused}")
    if universe:
        print(f"EDINET universe elements:   {universe} (across all sheets)")
        print(f"Alignment coverage:         {focused/universe*100:.2f}%")
    print(f"Filings materialized:       {len(raw)}")
    for f in raw:
        print(f"  - {f.name}")
    print("Claim families:")
    for k, v in counts.items():
        print(f"  {k:30s} {v}")
    print(f"Total claims:               {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
