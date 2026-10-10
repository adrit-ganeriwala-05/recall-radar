# DONE C→D: C9 capture script for submission/VIDEO_SHOTLIST.md shots 1–7
- From: C · To: D · Contract 1.0.0 · Shot list read from `origin/d/delivery`.

`BASE_URL=https://<rc1 deploy> npm --prefix web run capture` records 1920×1080 clips (`.webm`) + stills (`.png`) for
shots 1–7 into `web/test-results/captures/` (gitignored). It finds the hero via `/api/hero` (or `/demo/hero.json`),
drives the selector to the hero vehicle, pauses the replay on ▲ and again on ◆ "(later reveal)", opens the held-out
tab, and shows the issue page for the hero episode. It refuses to record if the SYNTHETIC TEST DATA banner is on
screen (`--allow-synthetic` for rehearsal). Shot 8 (Wi-Fi off + `make serve`) stays manual.
Rehearsed against the fixture-mode stub: all 7 shots recorded; the guard refuses without the flag.
One-time setup on the capture laptop: `npm --prefix web exec -- playwright install chromium` (= `make e2e-install`).

Also on c/web since PR #5 opened: lead-time histogram on results, episode markers on the vehicle timeline, the
received-date-experiment note in the header and on every screen (A3 chose LDATE_PLUS_7), replay agreement over
`exports/demo/replays/*`, and `web/HALLWAY_TEST.md` (C8 script + checklist).
