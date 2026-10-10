#!/usr/bin/env bash
# D5: upload the DuckDB file the API reads to the VM. Owner: D.
# Usage: bash deploy/sync_data.sh [path/to/recall_radar.duckdb] [--allow-large] [--yes]
#        make sync-data [DB=...]
# Prints size, SHA-256 and snapshot_id, uploads to data/recall_radar.duckdb.new, verifies the
# SHA-256 on the VM, swaps it in atomically and restarts the service if it is running.
# Plan (EXECUTION_PLAN D5): <= 500 MB -> this script. Larger -> upload the canonical zips and run
# `make pipeline` on the VM instead (deploy/README.md), unless --allow-large is given.
set -euo pipefail

on_vm() {
  local want=$1 data=/opt/recall-radar/data got
  got=$(sha256sum "$data/recall_radar.duckdb.new" | cut -d' ' -f1)
  [ "$got" = "$want" ] || { echo "ERROR: checksum mismatch on the VM ($got != $want)" >&2; exit 1; }
  chown rr:rr "$data/recall_radar.duckdb.new"
  chmod 644 "$data/recall_radar.duckdb.new"
  mv -f "$data/recall_radar.duckdb.new" "$data/recall_radar.duckdb"
  echo "$(date -u +%FT%TZ) data $want" >>/opt/recall-radar/DEPLOYS.log
  if systemctl is-active --quiet recall-radar; then
    systemctl restart recall-radar
    echo "service restarted on the new data"
  fi
  echo "VM data: $(ls -lh "$data/recall_radar.duckdb" | awk '{print $5}') sha256 $got"
}

if [ "${1:-}" = --on-vm ]; then
  shift
  on_vm "$@" </dev/null
  exit
fi

# ---------------------------------------------------------------- laptop side
# shellcheck source=deploy/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
rr_load_env
DB="" ALLOW_LARGE=0
while [ $# -gt 0 ]; do
  case $1 in
    --allow-large) ALLOW_LARGE=1; shift ;;
    --yes | -y) RR_YES=1; shift ;;
    -*) die "unknown option $1" ;;
    *) DB=$1; shift ;;
  esac
done
DB=${DB:-${RR_DATA_DIR:-$RR_ROOT/data}/recall_radar.duckdb}
[ -s "$DB" ] || die "no DuckDB file at $DB"
[ ! -e "$DB.wal" ] || die "$DB.wal exists: the database is open or not checkpointed; close the writer first"
BYTES=$(wc -c <"$DB" | tr -d ' ')
MB=$((BYTES / 1024 / 1024))
SHA=$(shasum -a 256 "$DB" | cut -d' ' -f1)
SNAP=$(cd "$RR_ROOT" && uv run --quiet python -c '
import sys, duckdb
con = duckdb.connect(sys.argv[1], read_only=True)
print(",".join(r[0] for r in con.execute("select distinct snapshot_id from source_snapshot order by 1").fetchall()) or "none")
' "$DB" 2>/dev/null || echo "unknown (no source_snapshot table)")
info "$DB: ${MB} MB, sha256 $SHA, snapshot_id $SNAP"
if [ "$MB" -gt 500 ] && [ "$ALLOW_LARGE" = 0 ]; then
  die "${MB} MB > 500 MB: per the plan, run the pipeline on the VM instead (deploy/README.md 'Large database'), or re-run with --allow-large"
fi
rr_confirm "Upload it to $RR_VM and swap it in (restarts the service)?"
rr_rsync --partial --progress "$DB" "$RR_VM:$RR_APP_DIR/data/recall_radar.duckdb.new"
rr_run_on_vm "${BASH_SOURCE[0]}" "$SHA"
info "data synced; record in docs/status/D.md: D5 rsync, ${MB} MB, sha256 ${SHA:0:12}, snapshot $SNAP"
