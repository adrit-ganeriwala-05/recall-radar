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
only data that was public at the time. Use it to read a vehicle's full complaint history and to
see what was public before each NHTSA investigation.

**0:35–1:35 · Demo: a replay from the development years.** (Chosen by a rule frozen before the
held-out run; no held-out case qualified, and the screen says "development period".) Pick the vehicle. Here is its complaint history for one component. Press play: each month
the detector sees only complaints that counted as public by then: seven days after NHTSA
received each one. ▲
marks the alert, with a plain-sentence explanation. Keep playing: ◆ marks the date NHTSA opened
the investigation, a later reveal the detector never saw. This is one case the detector got early;
the question is whether that happens more often than chance.

**1:35–2:15 · Results, honestly.** Thresholds were frozen before the held-out year, and so was
the bar: a margin above chance set before the evaluation. Read the results page's sentence as is:
[verdict.held_out]
In plain words: on the held-out year it did not. Every miss is listed on the results page, as are
alerts that never led to anything.

**2:15–2:40 · What an alert is not.** An alert is a pattern that deserves a closer look. It is not
a defect finding or a recall forecast, and NHTSA staff have data we don't. For any specific car,
the app sends you to NHTSA's VIN lookup.

**2:40–3:00 · How and next.** Public NHTSA data, a Poisson detector you can explain in one sentence,
a cached app on Vultr that also runs offline, and rules we froze before we saw the held-out
result. Next: test at the level of engineering analyses, with a new freeze and a new held-out year.
