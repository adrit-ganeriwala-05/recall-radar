#!/usr/bin/env bash
# Clean-clone reproducibility check. Owner: D (procedure), B (what must match).
# Clones HEAD into a temp dir, installs locked deps, reruns the full pipeline against the same
# raw snapshot, and compares the regenerated exports/demo files byte-for-byte with the committed
# ones. Usage: make repro   (needs RR_RAW_DIR pointing at the canonical, verified zips)
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$ROOT" rev-parse HEAD)"
RAW="$(cd "${RR_RAW_DIR:-$ROOT/data/raw}" && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/rr-repro-XXXXXX")"
echo "repro: commit $SHA, raw $RAW, workdir $WORK"
git clone --quiet --no-local "$ROOT" "$WORK/repo"
cd "$WORK/repo"
git checkout --quiet "$SHA"
git fetch --quiet --tags "$ROOT" 2>/dev/null || true
uv sync --locked --quiet
export RR_DATA_DIR="$WORK/data" RR_RAW_DIR="$RAW"
mkdir -p "$RR_DATA_DIR"
uv run python -m recall_radar.data.snapshot verify --raw "$RAW"
make --no-print-directory pipeline > "$WORK/pipeline.log" 2>&1 || { tail -n 40 "$WORK/pipeline.log"; exit 1; }
status=0
for f in results_development.json results_held_out.json results.csv cases.csv; do
  if [ -f "$ROOT/exports/demo/$f" ]; then
    if cmp -s "$ROOT/exports/demo/$f" "exports/demo/$f"; then echo "MATCH  $f"; else echo "DIFFER $f"; status=1; fi
  fi
done
( cd exports/demo && (sha256sum results*.json results.csv 2>/dev/null || shasum -a 256 results*.json results.csv) ) | tee "$WORK/repro_hashes.txt"
echo "repro: log $WORK/pipeline.log ; hashes $WORK/repro_hashes.txt ; exit $status"
exit $status
