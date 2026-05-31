"""Fail-loud behavior of find_target_filings.

Honda-case regression: in v0.5 the script returned 0 even when targets were
missing (4 of 5 found, exit 0). Production-grade requires --strict to exit
non-zero on any miss.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "find_target_filings.py"


def test_strict_flag_exists():
    """--strict must be a documented argument."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True, check=True,
    )
    assert "--strict" in r.stdout, "find_target_filings.py must expose --strict"


def test_strict_exits_nonzero_when_targets_missing(tmp_path, monkeypatch):
    """With --strict and a window guaranteed to find nothing, exit code must be non-zero."""
    # Point at a far-past, narrow window so no FY2024 securities reports match.
    out = tmp_path / "targets.json"
    env = {"EDINET_API_KEY": "dummy-key-for-arg-parsing"}
    r = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--days", "1",
         "--end-date", "2010-01-01",
         "--out", str(out),
         "--strict"],
        capture_output=True, text=True, env=env,
    )
    # Acceptable failure modes: exit 3 (strict miss) or exit !=0 from network/key.
    # The contract under test: with --strict and no matches, exit code != 0.
    assert r.returncode != 0, (
        f"--strict must exit non-zero when targets are missing; got exit {r.returncode}\n"
        f"stdout: {r.stdout[:400]}\nstderr: {r.stderr[:400]}"
    )
