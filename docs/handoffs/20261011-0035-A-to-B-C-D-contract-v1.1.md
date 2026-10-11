# HANDOFF A→B, C, D: contract v1.1.0 (PRD v2 §5), additive only
- From: A · To: B (ack), C (ack), D (merge first in the next window) · Contract: 1.0.0 → 1.1.0
- Commit: see the PR head; one commit: contracts.py + schema + TS + fixtures + tests + CONTRACTS.md.

## What changed (all new fields optional with defaults; nothing renamed, removed or re-typed)
- `RecallCampaign`: summary, consequence, remedy (official text, verbatim), park_it / park_outside
  (**StrictBool | None**: the contract never coerces "false"/"yes"/0/1, so normalisation happens once, at A's
  ingest), report_date_basis, source_url, snapshot_id, explanation (`RecallExplanation`).
- `RecallExplanation`: status accepted | fallback; ≤ 2 `ExplanationSentence` (≤ 45 words, source_fields ⊆
  summary/consequence/remedy, verbatim source_spans). A fallback carries no sentences (never labeled AI); an
  accepted one needs sentences, model and prompt_version.
- `ReplayMarker`: campno, link issue | vehicle (recall_reported markers; null elsewhere).
- New: `SymptomDoc`, `SymptomAlias`, `SymptomConcept`, `SymptomIndex` (≤ 2,000 docs, newest first, excerpts ≤ 400),
  `DateRange`, `ReportGroup`, `ReportInvestigation`, `ReportData` (≤ 5 groups, ≤ 5 investigations, ≤ 6 campaigns;
  shown_n = len(top_groups); totals for all three lists so each can say "showing n of m", PRD F8.2).
- Endpoints (CONTRACTS.md §6): `/api/symptom-index`, `/api/report` (A builds them in F7/F8).

## Fixtures (synthetic_fixture)
- `vehicle.json`: 3 recall cards — park_it true/park_outside false + accepted explanation; false/true + fallback;
  null/null + no explanation; one has markup-like characters and a line break in the official text.
- New `symptom_index.json` (3 docs, 2 aliases, 3 concepts incl. brake noise vs brake failure), `report.json`.
- Every fixture's provenance is now 1.1.0.

## For D
- `exports/demo/**` is untouched and still validates under 1.1.0, but those payloads say `contract_version` 1.0.0.
  `tests/integration/conftest.py` asserts `prov.contract_version == C.CONTRACT_VERSION`, so after this merges the
  release integration fails on results/hero/replays. Suggested: compare the major version only (1.x = compatible),
  per the CONTRACTS.md changelog line.
