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

## Redaction
- Independent token-based leak check (tests/data/test_redaction.py) over all 357,757 stored
  texts: 0 emails, phone-shaped numbers or VIN patterns after the fix in c015403 (was 1,444).
- Over-redaction is accepted: 10-digit numbers in any grouping (including part numbers like
  12345-67890) become [PHONE]; "<number> <words> <street suffix>" becomes [ADDRESS].
