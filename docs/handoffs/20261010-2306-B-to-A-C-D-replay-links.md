# REQUEST B→A (API), with a note for C and D: most "replay" links lead to an error
- From: B (watching) · To: A (owner of `recall_radar/api`), C (links), D (release decision) · Contract version: 1.0.0
- Found while checking PR #21 at main aed57f4; live site at bb1852f behaves the same. Nothing under the freeze is involved.

## What is wrong
The site links to `/replay/<episode_id>` from three places: every alert on a vehicle page ("replay"), every alert
on an issue page ("Replay this alert month by month"), and every results row that has a best episode. The API
serves a replay only if `exports/demo/replays/<id>.json` exists, and the bundle holds 21 of them (the early cases
and the hero). The database has 2,532 alert episodes. For the other 2,511 the page shows the error
"No replay exported for this alert episode."

- Results page: 85 rows have a replay link; 25 work (the 24 early rows, and one other row whose alert is also an
  early case's alert) and 60 do not (after official action, late, outside window; 54 in the development table,
  6 in the held-out table).
- Live check: `GET http://64.177.53.230/api/replay/E-014J` → 404.
- The demo path is not affected: the hero and every early case work, and D's smoke test follows the hero.

## Suggested fix (API only; tested here, not applied — it is A's file)
Build the replay from the database when no file was exported. The method code already does this for the export;
the only obstacle on the VM is that `replay_for_episode` takes its provenance from git, and a release has no git
checkout. The function below composes the same public pieces and takes the provenance from the API's `Store`.
It imports nothing new into the method package and changes no frozen file.

Tested on the frozen-run database (read-only connection):
- all 21 exported replays: output is byte-identical to the committed files when given their provenance;
- 150 other episodes chosen at random: identical to `replay_for_episode`, contract-valid, strict JSON;
- unknown id → `None` (keep the 404); about 0.2 s per call (median 0.21, max 0.26).

```python
"""Suggested fallback for GET /api/replay/{episode_id} when no file was exported (for A).

Uses only public functions of recall_radar.method (unchanged, under freeze-v1) and takes the
provenance from the API's own Store, so it works on the VM where there is no git checkout.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from recall_radar import contracts as C
from recall_radar.method import match as M
from recall_radar.method.detect import DetectorParams
from recall_radar.method.replay import BANNERS, FLAG_COLS, build_frames, build_markers


def replay_on_demand(cur: Any, cfg: dict[str, Any], provenance: C.Provenance, episode_id: str, cutoff: date) -> C.Replay | None:
    """The same replay `make export` writes, for any stored episode; None if the id is unknown."""
    h = cfg["config_hash"]
    eps = M.load_episodes(cur, h)  # the loader the export uses: dates as dates, contract order
    ep = eps[eps["episode_id"] == episode_id]
    if ep.empty:
        return None
    ep = ep.iloc[0]
    rows = cur.execute(
        f"""SELECT CAST(odino AS VARCHAR) AS odino, make, model, model_year, comp_system,
                   CAST(avail_date AS DATE) AS avail_date, {", ".join(FLAG_COLS)}
            FROM complaint_system WHERE make = ? AND model = ? AND model_year = ? AND comp_system = ?""",
        [ep["make"], ep["model"], int(ep["model_year"]), ep["comp_system"]],
    ).df()
    frames = build_frames(rows, ep["start_month"], DetectorParams.from_config(cfg), cutoff)
    outcome, recall_dates = None, {}
    m = cur.execute("SELECT * FROM alert_match WHERE episode_id = ? AND config_hash = ?", [episode_id, h]).df()
    if len(m):
        row = m.iloc[0].to_dict()
        for col in ("investigation_open_date", "follow_up_end"):
            row[col] = None if pd.isna(row[col]) else pd.Timestamp(row[col]).date()
        outcome = M.to_outcome(row)
    if outcome is not None and outcome.recall_campnos:
        found = cur.execute(
            """SELECT CAST(campno AS VARCHAR), min(CAST(report_date AS DATE)) FROM recall_campaign
               WHERE report_date IS NOT NULL AND list_contains(?, CAST(campno AS VARCHAR)) GROUP BY 1""",
            [outcome.recall_campnos],
        ).fetchall()
        recall_dates = {c: (d.date() if hasattr(d, "date") else d) for c, d in found}
    return C.Replay(
        provenance=provenance, episode_id=episode_id, group_id=ep["group_id"],
        vehicle=C.VehicleKey(make=ep["make"], model=ep["model"], model_year=int(ep["model_year"])),
        comp_system=ep["comp_system"], frames=frames,
        markers=build_markers(frames, eps[eps["group_id"] == ep["group_id"]], outcome, recall_dates), outcome=outcome,
        banner=BANNERS[cfg["availability"]["primary"]],
    )
```

In `replay()` in `recall_radar/api/main.py`, keep the exported file first (the hero and the early cases stay
byte-identical to the bundle, which D's displayed-vs-exported test compares) and fall back only when it is missing:

```python
p = s.export_file(f"replays/{episode_id}.json")
if p is None and s.db_path.is_file():
    r = replay_on_demand(store.cursor(), store.config, store.provenance, episode_id, data_cutoff(store.config, "full"))
    if r is not None:
        return ok(json.loads(replay_json(r)))   # recall_radar.method.replay.replay_json: the export's 6-decimal form
```
(`data_cutoff` is `recall_radar.method.util.data_cutoff`; names of the Store attributes are from my reading of the
file, adjust as needed.) An on-demand replay carries the API's provenance (deployed commit, `cached_real`), an
exported one carries the pipeline revision; both are correct for what they are.

## If there is no time for an API change
C can make the dead ends go away without the API: fetch `/demo/MANIFEST.json` once and render a replay link only
for episode ids listed under `replays/`, plain text otherwise. That hides the feature for most alerts instead of
providing it, but nothing leads to an error.

## Who decides
D: whether this goes into `rc1`. I review the API PR as soon as A posts it.
