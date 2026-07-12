# Governance Status

J-FIBO is currently a **single-author research artifact**. The intent is that
it becomes the J-FIBO Working Group's ontology over time, but as of now:

- No Japanese regulator (FSA, Bank of Japan, Digital Agency) has endorsed,
  reviewed, or participated in J-FIBO.
- No market operator (JPX/TSE) has endorsed, reviewed, or participated.
- No standards body (EDM Council, OMG, FISC, FDUA) has endorsed, reviewed,
  or participated.
- No formal working group exists.

The `registry/contributors.yaml` slot named `jfibo-wg-bootstrap` is a
placeholder for the eventual working group. The Japanese-bodies list in
its note is illustrative ("if such a group ever forms, these are the
bodies who might steward it"), not a participation claim.

Why mention them at all then: because future contributors *do* need a
slot, and the PROV machinery has to be in place before contributions can
be attributed term-by-term. The same way EDM Council *should* expose
FIBO term-level provenance but doesn't — J-FIBO is starting with that
substrate so it doesn't have to be retrofitted later.

## What is real today

- Materialized RDF derived from five EDINET filings (Toyota Motor Corp,
  ITOCHU, MUFG, SoftBank Group, and Honda Motor FY2024).
- Reproducible structural field-presence numbers grounded in those committed
  claim graphs. These are not independent extraction-accuracy or comparative
  ontology benchmarks.
- A real ontology with verified FIBO/Commons parents, closed vocabularies,
  and SHACL conformance.

## What is aspirational

- The "J-FIBO Working Group" name.
- Any future role of Digital Agency / FSA / JPX / FISC / FDUA / EDM Council
  Japan Chapter.
- The "Japan-wide universal financial ontology" framing.

This file is the public, unambiguous version of the disclaimer. The
README, vision document, and trajectory document all link here.
