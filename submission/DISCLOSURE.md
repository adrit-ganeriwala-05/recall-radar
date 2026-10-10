<!-- Owner: D. Paste into Devpost's disclosure field. -->

# Disclosure

- **Created before Hacklanta:** nothing of ours. No code, data processing or design predates the
  event (Oct 9–11, 2026). We used open-source libraries (Python, DuckDB, SciPy, pandas, FastAPI,
  Uvicorn, Pydantic, React, Vite, TypeScript, Recharts, Vitest, Playwright, Caddy) under their
  licenses.
- **AI assistance:** planning documents, contracts, coordination files and code were written with
  Claude (Anthropic) via Claude Code during the event, starting 2026-10-10. Every change was
  committed to the public repository; the git history shows who and when.
- **Data:** public NHTSA Office of Defects Investigation datasets (complaints, investigations,
  recalls) from https://www.nhtsa.gov/nhtsa-datasets-and-apis, downloaded 2026-10-10. Personal
  fields are dropped at parse time and complaint text is redacted before storage. The snapshot's
  file hashes are in `snapshots/SNAPSHOT.lock.json`.
- **No user data:** no accounts, cookies for tracking, or analytics.
