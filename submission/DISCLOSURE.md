<!-- Owner: D. Paste into Devpost's disclosure field. -->

# Disclosure

- **Created before Hacklanta:** nothing of ours. No code, data processing or design predates the
  event (Oct 9–11, 2026). We used open-source libraries (Python, DuckDB, SciPy, pandas, FastAPI,
  Uvicorn, Pydantic, React, Vite, TypeScript, Recharts, Vitest, Playwright, Caddy) under their
  licenses.
- **AI assistance:** planning documents, contracts, coordination files and code were written with
  Claude (Anthropic) via Claude Code during the event, starting 2026-10-10. Every change was
  committed to the public repository; the git history shows who and when.
- **AI in the product:** Google Gemini writes the plain-language recall explanations (each reviewed before
  publishing) and, in the iMessage assistant, interprets questions and rewords replies; every number and
  link in a reply is checked against our data first. Gemini runs on the free tier, where Google may keep
  and review what it is sent.
- **Third-party services:** Photon Spectrum carries the iMessage conversation; NHTSA vPIC decodes a VIN
  when a user presses Decode (from the user's browser).
- **Data:** public NHTSA Office of Defects Investigation datasets (complaints, investigations,
  recalls) from https://www.nhtsa.gov/nhtsa-datasets-and-apis, downloaded 2026-10-10. Personal
  fields are dropped at parse time and complaint text is redacted before storage. The snapshot's
  file hashes are in `snapshots/SNAPSHOT.lock.json`.
- **User data:** the website has no accounts, tracking cookies or analytics; "Remember this car" and the
  report draft stay in the browser. The iMessage assistant (off except in supervised test windows) stores,
  per chat, the chat handle, the watched vehicle with consent time, the vehicle from the last 30 minutes of
  conversation, and the replies it sent; DELETE removes all of it except a one-way hash.
