# Changelog

All notable changes to J-FIBO are recorded here. Dates are KST.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning: [SemVer](https://semver.org/spec/v2.0.0.html).

The repository version is authoritatively set in `pyproject.toml`.

## [1.1.1] — 2026-06-01

### Fixed
- Honda EDINET code corrected; Honda corpus materialized end-to-end (+57 claims).
- `find_target_filings`: defer `EDINET_API_KEY` check until after argparse so
  `--help` and dry runs work without a key (no-key-required contributor path).
- Honda corpus test now skips the raw-zip presence check when the corpus is
  not materialized locally (CI stays green; full check runs when zips exist).

### Docs
- README: make the "no EDINET API key required to contribute" policy
  explicit so external contributors can iterate against the shipped fixtures.

## [1.1.0] — 2026-06-01

### Added
- Bilingual JA coverage across labels and definitions.
- `MainBankCandidate` materializer.
- Source traceability documentation (`docs/source-traceability.md`).

### Changed
- `hasLender` domain fix.

## [1.0.0] — 2026-06-01

First version positioned as production-grade ontology.

### Added
- LCC / GLEIF external alignment.
- Honest coverage reporting (`docs/coverage.md`).
- CI with fail-loud targets so silent regressions surface immediately.

## [0.5.0] — 2026-05-25

### Added
- EDINET translation fidelity pass; width/depth coverage expansion.
- Repositioned the README and surrounding docs around the
  "dictionary, not application" framing.

## [0.4.0] — 2026-05-25

### Changed
- Reverted technical prefix back to `jfibo:` (brand name stays J-FIBO).
- README rewritten around the ontology framing rather than tooling.

### Docs
- Corrected license note: FIBO is MIT, and J-FIBO matches the upstream license.

## [0.2.0] — 2026-05-25

### Added
- Normative axis, holder roles, atomic claims.
- `jpfibo:` prefix (later reverted to `jfibo:` in 0.4.0).
- Building-trajectory PROV scaffolding.

## [0.1.0] — 2026-05-25

### Added
- Initial Japanese-finance ontology with EDINET alignment.

[1.1.1]: https://github.com/anthony0727/j-fibo/releases/tag/v1.1.1
[1.1.0]: https://github.com/anthony0727/j-fibo/releases/tag/v1.1.0
[1.0.0]: https://github.com/anthony0727/j-fibo/releases/tag/v1.0.0
[0.5.0]: https://github.com/anthony0727/j-fibo/releases/tag/v0.5.0
[0.4.0]: https://github.com/anthony0727/j-fibo/releases/tag/v0.4.0
[0.2.0]: https://github.com/anthony0727/j-fibo/releases/tag/v0.2.0
[0.1.0]: https://github.com/anthony0727/j-fibo/releases/tag/v0.1.0
