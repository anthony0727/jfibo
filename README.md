# J-FIBO (金融意味基盤・日本版)

> **Independent research artifact** — not endorsed by FSA, Digital Agency, JPX, BOJ, FISC, FDUA, EDM Council, or OMG. The `J-FIBO` brand and `jfibo:` prefix are provisional. See [`docs/governance-status.md`](docs/governance-status.md).

J-FIBO (金融意味基盤・日本版) is semantic infrastructure for Japanese finance — an OWL/SHACL ontology compatible with Japan's interoperability direction and aligned to [FIBO](https://spec.edmcouncil.org/fibo/) (EDM Council, MIT). It defines the Japanese securities-disclosure system as a semantic layer: legal forms, reporting regimes, disclosure document types, holder roles, ownership and financing concepts, and the institutional relationships that distinguish the Japanese market from other major jurisdictions. It extends [FIBO](https://spec.edmcouncil.org/fibo/) where FIBO already defines the parent concept, and aligns to the FSA-published EDINET XBRL taxonomy where the disclosure layer requires a reporting-tag mapping.

J-FIBO is not an AI benchmark, not an EDINET replacement, and not a database of facts. It is the meaning layer that lets banks, regulators, researchers, and (incidentally) AI consumers reason about Japanese disclosure on common ground.

## Scope (v1.0)

| Layer | What it covers |
|---|---|
| Legal entities | `KabushikiKaisha`, `GodoKaisha`, listed/unlisted, financial-institution sub-types (bank, trust bank, insurance, securities, asset management) |
| Reporting regimes | Companies Act · FIEL · Cabinet Office Ordinance on Disclosure · CG Code · JPX listing rules · TDnet |
| Disclosure documents | Annual / quarterly / semi-annual / extraordinary securities reports · large-shareholding reports · corporate-governance reports · tender-offer notifications |
| Holder roles | Beneficial · registered · trustee · nominee · custodian · strategic · pure-investment · policy |
| Ownership & financing | Shareholding, policy shareholding, specified investment shares, cross-shareholding, borrowings (short/long, syndicated), commercial paper |
| Institutional relationships | Keiretsu, business alliance, capital alliance, parent-subsidiary, listed-subsidiary, stable-shareholder, main-bank (candidate-only in v1.0) |
| External alignment | FIBO (`fibo-*`) · CMNS (`cmns-*`) · LCC (`lcc-*`) · GLEIF LEI · EDINET XBRL taxonomy |

## Conformance

| Check | Status |
|---|---|
| OWL parses, imports resolve, no undefined IRIs | Pass |
| Every public term has Japanese + English `skos:prefLabel` | Pass |
| Every stable term has a `dcterms:source` citation | Pass |
| SHACL shapes validate all `examples/valid/` | Pass |
| SHACL shapes reject all `examples/invalid/` with the expected constraint | Pass |
| Persistent `owl:versionIRI` on every module | Pass |
| OWL 2 RL profile (no constructs requiring DL/EL classification) | Pass |
| CI gates on every PR (pytest + ROBOT profile + pySHACL) | Pass |

See [`docs/coverage.md`](docs/coverage.md) for the honest scope of what is and isn't covered.

## Naming

| Surface | Form |
|---|---|
| Brand | **J-FIBO** (sibling of J-REIT, J-GAAP, J-SOX naming) |
| Repo / package / prefix / IRI | `j-fibo` / `jfibo` / `jfibo:` / `https://w3id.org/jfibo/` |

## Quick start

**No credentials required.** The default workflow is fully offline — the ontology, SHACL shapes, materialized claims (TTL), and all 47 tests live in the repo:

```bash
uv sync
uv run python scripts/build_ontology.py
uv run python scripts/validate.py examples/policy-shareholding-valid.ttl
uv run python -m pytest
```

That's everything a contributor needs to clone, run, and submit a PR.

### Optional: refresh the EDINET-aligned corpus

You only need this if you're adding a new filing or company to the materialized corpus. The raw EDINET ZIPs are gitignored and reproducible from the scripts below. Requires a free [EDINET API key](https://disclosure2dl.edinet-fsa.go.jp/) exported as `EDINET_API_KEY`:

```bash
export EDINET_API_KEY=...   # also accepted via ~/.env, never committed
uv run python scripts/download_edinet_taxonomy.py
uv run python scripts/build_edinet_focus.py
uv run python scripts/find_target_filings.py --days 400 --strict
uv run python scripts/edinet_client.py download <docID> --type 1
uv run python scripts/extract_xbrl_facts.py
uv run python scripts/parse_major_shareholders.py
uv run python scripts/parse_borrowings.py
uv run python scripts/materialize_claims.py
```

The `--strict` flag exits non-zero if any requested target filing is not found, so partial runs fail loudly.

## Contributing

J-FIBO is open source and contributions are welcome. **You do not need an EDINET API key to contribute** — the ontology, shapes, fixtures, and tests are all checked in, and CI runs entirely offline.

| Contribution type | EDINET key needed? |
|---|---|
| Docs, typos, ontology edits, SHACL shapes, new fixtures, new tests | No |
| Refactoring scripts under `scripts/` | No |
| Adding a *new* EDINET filing / company to the materialized corpus | Yes (local only — CI does not need it) |

CI on every PR runs `uv run python -m pytest` plus SHACL positive/negative validation and an OWL-profile check. All gates pass without credentials.

## Layout

```
ontology/         OWL/TTL modules — meaning layer
shapes/           SHACL shapes — conformance layer
registry/         YAML source of truth for terms / entities / contributors / sources
examples/         Validation fixtures (valid + invalid)
scripts/          Builders, EDINET extractors, materializers
benchmark/        Production benchmark — semantic and EDINET-claim coverage
tests/            Pytest suite (47 tests)
docs/             Governance, coverage, release, source, design policies
research/         Non-production research material (AI-eval cases, etc.)
data/             Mostly gitignored; reproducible via scripts/
```

## Related work, not part of this repo

- **`jp-finance-agent-benchmark`** (planned, separate repo) — trap-family benchmarks for AI agents on Japanese-finance reasoning. Uses J-FIBO as the semantic anchor but is not J-FIBO.

## License

[MIT](LICENSE) — both code and ontology. Matches upstream FIBO.
