<!-- Owner: D. Reviewer: C. Judge questions with short, honest answers. Numbers only as
period.metric placeholders in square brackets (filled into submission/out/QA.md). Rehearse at 2:45 AM. -->

# Judge Q&A

**Does this forecast recalls or find defects?** No. An alert says a complaint pattern grew unusually
fast for one vehicle and component and deserves a closer look. We compare alerts with documented
investigation opening dates afterwards; we never label a vehicle.

**Did you beat NHTSA?** We make no such claim. NHTSA staff use data we don't have (manufacturer
reports, field data). We only compare with the public opening date.

**How do you avoid using future data?** Each complaint counts as public seven days after NHTSA
received it; at every replay cutoff the detector sees only complaints public before it. Investigation and recall tables
are never read by detector code (a test drops them and checks the output is identical). A
property test adds future complaints and checks no earlier score changes.

**Why not the "added to file" date?** In today's files it equals the received date for almost
all complaints, so it looks rewritten and cannot show when a record became public. We decided at
our first checkpoint to use the received date plus seven days instead, and every screen labels the
replay a "received-date experiment". Current files also reflect later corrections; the UI says
the replay uses today's records and labels.

**How good is it?** On the held-out year, with thresholds frozen first: early alerts for
[held_out.early_coverage_all] of eligible investigations (95-percent interval
[held_out.early_coverage_all.ci_low]–[held_out.early_coverage_all.ci_high]) versus
[held_out.chance_coverage] for matched controls. All misses are listed. The results page says it
in one sentence:
[verdict.held_out]

**So the detector does not work?** Not as an early-warning signal on the held-out year, and we
say so on the results page and here. What the app does do is let anyone read a vehicle's full
complaint history and see what was public before each NHTSA investigation. The replay in the
demo is a development-period case and is labeled that way.

**What is "chance" here?** For each investigated vehicle and system we pick up to five similar
vehicles (same system, nearby model year, similar prior volume, no investigation) and run the
same detector. Their alert rate is the baseline.

**Why Poisson and not a neural model?** Every alert must be explainable in one sentence and
checkable by hand. With this little signal per vehicle, a transparent baseline is the honest start.

**What about privacy?** Names, addresses, VINs, dealer and location fields are dropped at parse
time; excerpts are regex-redacted and shown truncated with a link to the public NHTSA record.
No accounts, no tracking.

**Can I reproduce it?** `make setup && make pipeline` on the snapshot recorded in
`snapshots/SNAPSHOT.lock.json`; `git checkout baseline-v1 && make repro` compares the result files (both period summaries, results.csv, cases.csv) byte for
byte (hash in Devpost).

**What's next?** Most held-out investigation families were excluded because their first action was an
engineering analysis, almost all of them from a single analysis that names several hundred
vehicle and system combinations ([held_out.excluded_families.numerator] of
[held_out.excluded_families.denominator] families excluded for any reason). The next test is at that level, with a new freeze and
a new held-out year.
