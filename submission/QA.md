<!-- Owner: D. Reviewer: C. Judge questions with short, honest answers. Numbers only as
period.metric placeholders in square brackets (filled into submission/out/QA.md). Rehearse at 2:45 AM. -->

# Judge Q&A

**Does this forecast recalls or find defects?** No. An alert says a complaint pattern grew unusually
fast for one vehicle and component and deserves a closer look. We compare alerts with documented
investigation opening dates afterwards; we never label a vehicle.

**Did you beat NHTSA?** We make no such claim. NHTSA staff use data we don't have (manufacturer
reports, field data). We only compare with the public opening date.

**How do you avoid using future data?** Each complaint has an "added to file" date; at every
replay cutoff the detector sees only complaints added before it. Investigation and recall tables
are never read by detector code (a test drops them and checks the output is identical). A
property test adds future complaints and checks no earlier score changes.

**Isn't the "added to file" date itself rewritten later?** Partly; current files reflect later
corrections. The UI says the replay uses today's records and labels. If those dates were
unreliable, we would have switched to the received date plus seven days and labeled it.

**How good is it?** On the held-out year, with thresholds frozen first: early alerts for
[held_out.early_coverage_all] of eligible investigations (95-percent interval
[held_out.early_coverage_all.ci_low]–[held_out.early_coverage_all.ci_high]) versus
[held_out.chance_coverage] for matched controls. All misses are listed.

**What is "chance" here?** For each investigated vehicle and system we pick up to five similar
vehicles (same system, nearby model year, similar prior volume, no investigation) and run the
same detector. Their alert rate is the baseline.

**Why Poisson and not a neural model?** Every alert must be explainable in one sentence and
checkable by hand. With this little signal per vehicle, a transparent baseline is the honest start.

**What about privacy?** Names, addresses, VINs, dealer and location fields are dropped at parse
time; excerpts are regex-redacted and shown truncated with a link to the public NHTSA record.
No accounts, no tracking.

**Can I reproduce it?** `make setup && make pipeline` on the snapshot recorded in
`snapshots/SNAPSHOT.lock.json`; `make repro` compares the exports byte for byte (hash in Devpost).

**What's next?** <one item from the measured results, e.g. the largest miss category>
