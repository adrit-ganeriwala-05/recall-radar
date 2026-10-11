# Baseline certificate — Recall Radar v1 (Gate A, PRD_v2 §8)

Owner: D · Measured 2026-10-11 00:18–00:35 ET on a detached checkout of `origin/main`.
The human's draft of this file was not received; every row below is D's own measurement or a
named teammate's posted result. Anything not measured says so.

## Identity
| Item | Value |
| --- | --- |
| Baseline code SHA | `195ad4561b4e1b3c157371bddf40f93cbaa44edf` (main after PR #21) |
| Tag | `baseline-v1` → 195ad45 (pushed only after the human approves) |
| Excluded from the baseline | `d/release` (PR #19: README, Devpost repro hash, gate log, domain script quoting) — unreviewed at Gate A; merges through C's review in the Stage B window |
| Freeze | `freeze-v1` → dd6b439, config hash `0c26e23e0a3a` |
| Snapshot | `e808281f001a` (availability basis LDATE_PLUS_7) |
| Export run ids | `development-0c26e23e0a3a-1c8dd4b`, `held_out-0c26e23e0a3a-1c8dd4b` |
| Serving DB | `recall_radar.duckdb`, 412 MB, sha256 `5d708042133cfb2888321a697a1fdb9838b910c9d5d1b9bac1542af01a438663` (sha verified on the VM) |
| Deployed | https://recall-radar.us (Let's Encrypt, apex + www; http → https 308) and http://64.177.53.230; `/healthz` → git_sha 195ad45…, mode cached, snapshot e808281f001a |
| Last-known-good | `lkg-g3` → 90f454c |

## Checks at 195ad45
| Check | Command | Result | Status |
| --- | --- | --- | --- |
| Setup | `make setup` | exit 0 | verified |
| Unit, lint, guards | `make check` | exit 0: 344 passed, 1 xfailed (python); 106 passed (web); secrets 0; claims 0; fill_numbers 0 | verified |
| Real data (D's machine) | `make test-real` with the serving DB | method 5/5, api 4/4, data 2/3 — the failure is `test_real_raw_dir_matches_committed_lock` (no raw zips on D's machine) | partial |
| Real data with raw zips | A: `RR_RAW_DIR=~/rr-raw make test-real` | **FAIL at 195ad45**: `test_real_alias_table_leaves_no_punctuation_variants` hard-coded `data/` → fix PR #23 (test-only); re-run at the merged SHA | **GATE A FAIL → A** |
| Deployed SHA | `curl /healthz` | git_sha = 195ad45 | verified |
| Integration | `RR_BASE_URL=https://www.recall-radar.us RR_RELEASE=1 RR_EXPECT_SHA=195ad45 make integration` | 21 passed, 0 skipped (displayed = exported) | verified |
| Browser smoke | `BASE_URL=https://www.recall-radar.us make e2e` | 2 passed (desktop, phone) | verified |
| Outage | `RELEASE=1 bash deploy/outage_check.sh --release` | 0 FAIL, 0 WARN | verified |
| Reproducibility | B: `RR_RAW_DIR=~/rr-raw make repro` at 195ad45 (PR #24 comment) | MATCH ×4 | verified (B) |
| Method + freeze (B) | `uv run pytest tests/method`; real_data method on DB 5d708042…; freeze check; `exports/demo` vs MANIFEST | 150 passed + 1 xfailed; 5 passed; ok; 26 files == MANIFEST | verified (B) |
| Protected tables | B: independent rebuild vs serving DB | checksum-identical | verified (B) |
| Web (C) | `npm ci && typecheck && test && build`; deployed browser pass at 360 px live and API-down | 106 passed; flows ok; console clean | verified (C stand-in) |

The checks ran against `https://www.recall-radar.us` because D's laptop still had a cached negative
DNS answer for the apex; the apex was checked separately with `curl --resolve` (200, valid certificate).

## Protected artifacts — sha256 of `exports/demo/**` at 195ad45 (27 files)
Gate B compares these byte for byte (PRD_v2 §1 "Frozen science").

| File | sha256 |
| --- | --- |
| `MANIFEST.json` | `614ccaad31e35d63c2049e4a36ef63a13d5f696c52787900b35f559a6986b726` |
| `cases.csv` | `df773929e0dc60d80817abfc5830962ee052e894fa946c1ab0e0fa5ca90a0bd5` |
| `hero.json` | `7a13ca3cb78ce7625e35425fd4c33973c3f0c1b332837b2fe2ffc5c443f79523` |
| `replays/E-00KQ.json` | `ae8f6d7d33bb01b5f34a7970cc15364283e4f19f4151f83291181857c0c6dc2c` |
| `replays/E-00Q0.json` | `c0ef8a098d2ba6ee0f36ed26381f8a1b28f3715eaa13d7df77b8322e6959f930` |
| `replays/E-00TK.json` | `1015bf33f7f95d7f7459da188b7a1f38bd802d08bbac8123281723d32c39a174` |
| `replays/E-00TN.json` | `9fef989466e9c3cf2900b1b67879b7a0c1db85814b904c9bfbf9b5e52be0143e` |
| `replays/E-00TO.json` | `ee170b578a1ca3f71320a81b96d17218af236c8b16ef231fb40c213a25a9b598` |
| `replays/E-00U4.json` | `7271c0739e3d82ac38bd04c6603c600e5e33777d75392e0d21873fc69fd1b527` |
| `replays/E-00UF.json` | `d3c1fb4ef9d5d47f74cb46dc332c74454dd13f761741e63d16bd789f6c3db9d6` |
| `replays/E-00UI.json` | `39ea7dcd2abe1bc3a4faaadea00018bc31ee573adc40076eae86b8224f01ee32` |
| `replays/E-00UT.json` | `18c57495da5cdb6bd15b8bce079695a8f7215508e79e75e3e508802d62bf4d20` |
| `replays/E-00VC.json` | `74325f908b89018f605cb460bfa42d750dcd1d043950c0424d5b3ce182d77d26` |
| `replays/E-00WG.json` | `18ae27d174da538177b127caa44d3cad0dad75426365f7867cfb9069039ecb88` |
| `replays/E-0109.json` | `9407da91cc113902ea5280b89aaf208c4744a0419efb93eca13577c981b64f36` |
| `replays/E-010B.json` | `485289d99f7ace65953a773804451ccaf8451f4d7c61ab09bbda7f0ff2da5210` |
| `replays/E-010O.json` | `55e425852f4a26f05ad331d7290f7206b1e5c2f5040b909cb1ec04e6d0f9dbfc` |
| `replays/E-011F.json` | `0148c1548b735f4f300d1fd62cdeb69a855444145bad8d08c7adbbcee9037007` |
| `replays/E-011Z.json` | `ed7344cc5b33c76cb2bbc1bdada15375ce4b2f95a878b781ddd2d4328f7866e9` |
| `replays/E-013G.json` | `48f5e7ff06f9b6e3631236c0995fffd12571c6e178f725595ecf979b3c8d789d` |
| `replays/E-0167.json` | `d4f6f827e28a8613ec0da1f4353d7ee7b4493eefaee60e7891e6a100b81feae1` |
| `replays/E-0179.json` | `affdb8c515fa4ce3f0b9f5bf809f79ddaa8979209a42a6e6db8192b2c205c1cd` |
| `replays/E-017A.json` | `e3d9937408fbbc580c1322911a637cacb5a9255a8f7c6cbc47359e23c46d9026` |
| `replays/E-017O.json` | `865cde41509126fac3ae74639eb696792e9cb266d83d704edc6f9a03abdceac7` |
| `results.csv` | `7a469c93a4097df1bb3d3f28a97772d20e58aa9ed106338cde6b67a3c561321a` |
| `results_development.json` | `fc16cb8519d89e66ee08915c6cf1ef089154fd8ba197943c108533309f6900ad` |
| `results_held_out.json` | `6c2245101c3928245587844214617964f7f5f535207cc77b65d8b0b1326c5c88` |
