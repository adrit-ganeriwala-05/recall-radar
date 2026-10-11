# Data notes (owner: A)

Findings from the real snapshot `e808281f001a` (files listed in `snapshots/SNAPSHOT.lock.json`).
Numbers here are data-quality counts from `ingest_report`, not evaluation results.

## Complaints, gate1 scope (COMPLAINTS_RECEIVED_2015-2019.zip)
- 489,809 lines, all with the 51 fields of CMPL.txt (fields 50–51 added April 2026); UTF-8.
- Ledger: read 489,809 = retained 485,078 + excluded 4,731 (4,727 non-vehicle products,
  4 dropped complaint types) + rejected 0 + deduplicated 0.
- 357,759 distinct complaints; 441,940 complaint × system rows over 40 systems; model year
  unknown for 1,127 (0.32%); dup_text flags 6,554.

## Availability: decision LDATE_PLUS_7 (Gate 1, 2026-10-10)
`logs/datea_lag.csv` has DATEA − LDATE per received month for 2015–2019:
- In every month at least 99.73% of complaints have DATEA = LDATE; p99 lag is 0 days in
  every month; overall 99.94%. Only 2 of 357,759 fail the 0–365-day rule.
- The largest single DATEA value holds 0.14% of complaints, so there is no cluster on one
  rewrite date. The fallback share is far under 5%.

Neither literal trigger in PROJECT_SPEC §5 fires. But a field that equals the received date
for practically every complaint is not evidence of when the record became public; it looks
rewritten (CMPL.txt documents the May 2021 system update). Using it would claim complaints
were visible the day NHTSA received them. **Decision: `availability.primary = LDATE_PLUS_7`**,
the more cautious basis, as B also suggested in the PR #4 review. Every screen then says
"received-date experiment" (PROJECT_SPEC §5).

## Investigations (FLAT_INV.zip) and recalls (FLAT_RCL_POST_2010.zip)
- INV: 154,429 vehicle rows, all 11 fields; 5,349 action numbers, 108 without a valid ODATE
  (dropped, counted). Types from the prefix: PE 2,330, EA 1,933, DP 506, RQ 210, AQ 43,
  other prefixes (SQ, EQ, ID, TA, RP, C8, C9) 219 → OTHER.
- Prefix check: 20 sampled actions all had the expected type. The two digits after the
  prefix match the ODATE year for 99.2% of actions opened since 2014; the rest are numbered by
  federal fiscal year (e.g. EA81002 opened 1980-10-07). One older number has a letter O
  (EA78O34); kept as is.
- Families: 8,707 written, 742 RQ/AQ-only not written. One investigation often covers several
  vehicles, and families are per (make, model, system), so 6,821 family ids carry the
  `~<hash>` suffix. 188 PE/DP-first families opened 2017–2019 come from 48 investigations.
- Of those 188, 122 (64.9%) have a complaint group with the same make, model, system and a model
  year in range; 167 (88.8%) match on make, model and year with any system. The gap is the
  INV component name vs. the complaint COMPDESC system (tier-2 system map, owner B).
- Recall report date field: **RCDATE** (Part 573 report received date). Only RCLTYPECD = V rows
  are kept: 108,942 rows, 13,673 campaigns; no null RCDATE.

## Full scope (A4: 2014 baseline + 2015–2019 + 2020–2023), built 2026-10-10 17:04 ET
- Config: b/method `config.yaml` @ f53b396 (config hash 419a39bbf60b, availability LDATE_PLUS_7).
- Ledger: read 1,301,663 = retained 914,165 + excluded 387,498 (366,853 received outside
  2014–2023, 20,633 non-vehicle products, 12 dropped types) + rejected 0 + deduplicated 0.
- 658,677 complaints (≈ 49k–77k per received year), 831,677 complaint × system rows,
  4,319 make/model pairs; model year unknown 0.28%.
- DATEA = LDATE for 99.93% of all 2014–2023 complaints: LDATE_PLUS_7 holds for the full range.
- Alias table `recall_radar/data/aliases.csv`: 150 rows, 145 groups, built from complaint,
  investigation and recall names whose letters+digits match exactly (C 300 → C300, F150 → F-150,
  !MX-5 → MX-5). Canonical = most complaints, then shortest, then alphabetical. Semantic
  aliases (trims, body styles) are deliberately not merged; F-150 and F-250 stay apart.
- Families (all years): 8,648; development-period (opened 2016–2019) PE/DP-first families: 268
  from 67 investigations, 170 (63.4%) with a same-system complaint group.
- Runtime: ingest 54–107 s (machine load), investigations 6 s; peak memory 4.6 GB;
  DB 344 MB built fresh.

## Redaction
- Independent token-based leak check (tests/data/test_redaction.py) over all 357,757 stored
  texts: 0 emails, phone-shaped numbers or VIN patterns after the fix in c015403 (was 1,444).
- A4 adds 7-digit local numbers (555-0134, 555 (0134) and wider separators; full scope:
  0 of 658,675 stored texts flagged by either checker (`pytest -m real_data`).
- Over-redaction is accepted: 10-digit numbers in any grouping (including part numbers like
  12345-67890) become [PHONE]; "<number> <words> <street suffix>" becomes [ADDRESS].

## A9 (release check, 2026-10-10 22:30)
- 1,004 excerpts fetched from the live site's `/api/issue` (http://64.177.53.230, main f324b00, real
  data): 0 emails, phone numbers or VINs; every excerpt ≤ 400 characters. A name scan beyond the
  ingest rules found a person named after an honorific (a manufacturer employee quoted from a
  letter): "MS. <first> <last>". Across all 658,677 stored texts, 349 contain an honorific + word.
- Fix at serving time, not at ingest: `recall_radar/data` is a pipeline input under freeze-v1, so
  `recall_radar/api/main.py` `scrub_names` replaces MR./MRS./MS./DR. (and MR/MRS without a period)
  + one or two following words with [NAME], keeping common words and part names ("MRS CONTROL
  UNIT", "MR TIRE"). Stored texts keep the ingest redaction; what the site serves gets both.
  332 stored texts change. Re-scan of 1,004 served excerpts with the fix: 0 names flagged.
- Mixed case (B's review of #15/#17): 141,602 stored texts are sentence case, and the first pattern was
  uppercase-only, so "Ms. Jane Doe" passed. The title now matches in any case and name words need a
  capital initial; common words are compared in uppercase. Full scan, title + period + capitalised
  non-common word: 346 texts before, 0 after (0 in served excerpts); 388 texts change.
- Known residual: "MS" without a period followed by a surname is not scrubbed, because "MS" is far
  more often Mississippi. Moving `scrub_names` into ingest is a post-hackathon change (needs a new
  freeze; the DB would be rebuilt).
- Post-deploy re-scan (main 2d3b0a1 live): 1,007 served excerpts → 0 names; the found complaint shows [NAME].
  It flagged a street address with a suffix the ingest rule lacks ("<number> AUTO PARK WAY", a dealer).
  The rule knows STREET…HIGHWAY but not WAY, PIKE, LOOP, FREEWAY, EXPRESSWAY, TURNPIKE, PLAZA, SQUARE;
  some matches are homes ("<number> <name> WAY"). `scrub_addresses` in the API adds them, with the
  ingest rule's speed/distance exclusions, and skips phrases (a common word between number and
  suffix: "2009 ALL THE WAY"). 1,871 stored texts change; a sample of 30 scrubbed spans is all
  addresses or highway exits. Known miss: "<number> THE <name> WAY".
- Displayed-vs-exported: `RR_RELEASE=1` integration against the live site and the browser field
  checks are recorded in docs/status/A.md.

## F1 recall cards (PRD v2, 2026-10-11)
- **Source fields** (`~/rr-raw/RCL.txt`, FLAT_RCL_POST_2010, all 245,855 rows have the 29 fields): summary =
  field 20 `DESC_DEFECT` CHAR(6000); consequence = 21 `CONEQUENCE_DEFECT` CHAR(2000) (NHTSA's spelling); remedy =
  22 `CORRECTIVE_ACTION` CHAR(6000); report date = 16 `RCDATE` "Part 573 Defect/Noncompliance Report Received
  Date" (basis label "Report received date (RCDATE)"; the v1 `recall_campaign.report_date` is the same field);
  do-not-drive = 28 `DO_NOT_DRIVE` CHAR(3); park-outside = 29 `PARK_OUTSIDE` CHAR(3). The three text fields are
  never empty in this snapshot. Flag values are exactly "Yes" (2,129 / 1,288 rows) or "No".
- **No API enrichment.** The flat file has every field (PRD F1.4 applies only if it lacks them), so no
  recallsByVehicle calls were made; the build is offline (a test fails it on any socket use).
- **Flags** (`recall_v2.normalize_flag`): true / "true" "y" "yes" (any case) → true; false / "false" "n" "no" →
  false; anything else → unknown (null; no banner). Per card a flag is known only if every source row that states it
  agrees.
- **Source link.** nhtsa.gov answers scripted requests with 403 (curl -I, a browser user agent, and headless
  Chromium: "Access Denied") for `/recalls?nhtsaId=18V332000`, `20V746000`, `21V035000` and for `/recalls` itself,
  so per-campaign deep links cannot be verified. Cards link to https://www.nhtsa.gov/recalls.
- **Table** `recall_campaign_v2`: one row per (campno, make, model, model_year) for RCLTYPECD 'V' with a valid
  year; same make/model normalisation and alias table as complaints, so cards never match on component alone.
  Real build: 219,104 vehicle rows → 93,362 cards, 13,556 campnos, identical key set to v1 `recall_campaign`;
  1,375 do-not-drive and 648 park-outside cards; 0 unknown flags; 0 campaigns with differing text across rows.
- **v2 DB** `$RR_DATA_DIR/recall_radar_v2.duckdb` = byte copy of the baseline DB + `recall_campaign_v2` + B's
  `recall_explanation`, `symptom_alias`, `symptom_concept` (attached read-only from `b_v2_tables.duckdb`). Build:
  `uv run python -m recall_radar.data.recall_v2 --baseline <recall_radar.duckdb> --out <recall_radar_v2.duckdb>
  --raw ~/rr-raw --b-tables <b_v2_tables.duckdb>` (12 s). It fingerprints every baseline table (rows + md5 over
  sorted row md5s) before and after and fails on any difference: 17 of 17 identical on A's build;
  `recall_radar.b_v2.protect` → PROTECTED TABLES: IDENTICAL.
