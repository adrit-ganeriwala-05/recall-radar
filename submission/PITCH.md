<!-- Owner: D. Reviewer: C. Three-minute pitch and video voiceover. Numbers only as
period.metric placeholders in square brackets; `make submission` fills them from exports/demo/results.csv into
submission/out/PITCH.md. A beat whose number is not measured is cut, never reworded with a guess. -->

# Pitch (three minutes)

**0:00–0:20 · The problem.** NHTSA receives a steady stream of vehicle complaints and
publishes all of them. The files are public, but nobody can read them as they arrive. The question
we asked: could a simple, transparent detector have flagged a complaint pattern before an
investigation was opened, using only what was public then?

**0:20–0:35 · The promise.** Recall Radar shows when owner complaints about the same vehicle and
problem started growing unusually fast, and whether NHTSA later opened an investigation, using
only data that was public at the time.

**0:35–1:35 · Demo: the hero replay.** (Hero chosen by a rule written and frozen before the
held-out run.) Pick the vehicle. Here is its complaint history for one component. Press play: each month
the detector sees only complaints whose records say they were available before that date. ▲
marks the alert, with a plain-sentence explanation. Keep playing: ◆ marks the date NHTSA opened
the investigation, a later reveal the detector never saw. Across held-out early cases the alert
came first by a median of [held_out.median_lead_days] days.

**1:35–2:15 · Results, honestly.** Thresholds were frozen before the held-out year. On it, the
detector alerted early for [held_out.early_coverage_all] of eligible investigations, against
[held_out.chance_coverage] for matched control groups. Every miss is listed on the results page,
as are alerts that never led to anything.

**2:15–2:40 · What an alert is not.** An alert is a pattern that deserves a closer look. It is not
a defect finding or a recall forecast, and NHTSA staff have data we don't. For any specific car,
the app sends you to NHTSA's VIN lookup.

**2:40–3:00 · How and next.** Public NHTSA data, a Poisson detector you can explain in one sentence,
a cached app on Vultr that also runs offline. Next: <one measured next step from QA.md>.
