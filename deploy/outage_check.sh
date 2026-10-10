#!/usr/bin/env bash
# Prove the deployed release serves every screen with ALL outbound traffic blocked. Owner: D.
# Usage: bash deploy/outage_check.sh [--release]          (make outage-check [RELEASE=1])
# On the VM it (1) shows that a sandbox with IPAddressDeny=any really cannot reach the internet,
# (2) starts a second instance of the current release on 127.0.0.1:8001 inside that sandbox
# (systemd-run -p IPAddressDeny=any -p IPAddressAllow=localhost), (3) requests every endpoint of
# CONTRACTS.md section 6 plus the web app, following the hero vehicle when a hero exists, and
# (4) stops the instance. Without --release, results/hero/replay may answer 503 "unavailable"
# (exports not built yet); with --release (Gate 3/4) every request must return 200.
set -euo pipefail

on_vm() {
  local release=${1:-0} app=/opt/recall-radar port=8001 unit=rr-outage-check
  local base=http://127.0.0.1:8001 fails=0 warns=0 RR_MODE=cached RR_GIT_SHA=""
  [ -d "$app/current" ] || { echo "ERROR: no current release" >&2; exit 1; }
  # shellcheck disable=SC1091
  [ ! -f "$app/current/.deploy.env" ] || . "$app/current/.deploy.env"
  # literal unit name: the EXIT trap runs after on_vm's locals are gone
  cleanup() { systemctl stop rr-outage-check 2>/dev/null || true; systemctl reset-failed rr-outage-check 2>/dev/null || true; }
  trap cleanup EXIT
  cleanup

  if systemd-run --quiet --wait --pipe --collect -p IPAddressDeny=any -p IPAddressAllow=localhost \
    curl -sS -m 5 -o /dev/null https://static.nhtsa.gov/ 2>/dev/null; then
    echo "FAIL sandbox: outbound HTTPS still works inside the sandbox, so this check proves nothing"
    exit 1
  fi
  echo "PASS sandbox blocks outbound traffic (curl https://static.nhtsa.gov failed inside it)"

  systemd-run --quiet --unit="$unit" --uid=rr --gid=rr \
    -p IPAddressDeny=any -p IPAddressAllow=localhost -p WorkingDirectory="$app/current" \
    --setenv=RR_MODE="$RR_MODE" --setenv=RR_DATA_DIR="$app/data" --setenv=RR_GIT_SHA="$RR_GIT_SHA" \
    --setenv=PYTHONUNBUFFERED=1 \
    "$app/current/.venv/bin/uvicorn" recall_radar.api.main:app --host 127.0.0.1 --port "$port"
  local up=0
  for _ in $(seq 1 60); do
    if curl -fsS -m 2 "$base/healthz" >/dev/null 2>&1; then up=1; break; fi
    sleep 0.5
  done
  [ "$up" = 1 ] || { journalctl -u "$unit" -n 40 --no-pager; echo "FAIL offline instance did not start"; exit 1; }
  echo "PASS offline instance up on :$port (mode $RR_MODE, release ${RR_GIT_SHA:0:7})"

  BODY=""
  # check <path> <required: 1|0> — 200 passes; 503 "unavailable" is a WARN unless required.
  # A .json/.csv path answered with HTML is the SPA fallback (file missing), not a pass.
  check() {
    local path=$1 required=$2 code ctype
    read -r code ctype < <(curl -sS -m 15 -o /tmp/rr-outage-body -w '%{http_code} %{content_type}\n' "$base$path" || echo "000 none")
    BODY=$(cat /tmp/rr-outage-body 2>/dev/null || true)
    if [ "$code" = 200 ] && [[ $path =~ \.(json|csv)$ ]] && [[ $ctype == text/html* ]]; then
      code="200-html"
    fi
    if [ "$code" = 200 ]; then
      echo "PASS 200 $path"
    elif [ "$code" = 200-html ] && [ "$required" = 0 ]; then
      echo "WARN missing file (SPA fallback HTML) $path"
      warns=$((warns + 1))
      BODY=""
    elif [ "$code" = 503 ] && [ "$required" = 0 ] && [ "$(jq -r '.error.code? // empty' <<<"$BODY" 2>/dev/null)" = unavailable ]; then
      echo "WARN 503 unavailable $path"
      warns=$((warns + 1))
      BODY=""
    else
      echo "FAIL $code $path"
      fails=$((fails + 1))
      BODY=""
    fi
  }
  enc() { jq -rn --arg v "$1" '$v|@uri'; }

  local optional=1
  [ "$release" = 1 ] && optional=0
  local need=$((1 - optional))
  check /healthz 1
  check /api/meta 1
  check / 1
  check /results 1
  check "/api/results?period=development" "$need"
  check "/api/results?period=held_out" "$need"
  check "/api/export/results.csv?period=development" "$need"
  check /api/hero "$need"
  local episode="" make="" model="" year="" group=""
  episode=$(jq -r '.episode_id // empty' <<<"$BODY" 2>/dev/null || true)
  if [ -n "$episode" ]; then
    check "/api/replay/$(enc "$episode")" 1
    make=$(jq -r '.vehicle.make // empty' <<<"$BODY")
    model=$(jq -r '.vehicle.model // empty' <<<"$BODY")
    year=$(jq -r '.vehicle.model_year // empty' <<<"$BODY")
    group=$(jq -r '.group_id // empty' <<<"$BODY")
    check "/demo/hero.json" "$need"
  fi
  check /api/makes 1
  [ -n "$make" ] || make=$(jq -r '.items[0] // empty' <<<"$BODY")
  check "/api/models?make=$(enc "$make")" 1
  [ -n "$model" ] || model=$(jq -r '.items[0] // empty' <<<"$BODY")
  check "/api/years?make=$(enc "$make")&model=$(enc "$model")" 1
  [ -n "$year" ] || year=$(jq -r '.items[-1] // empty' <<<"$BODY")
  check "/api/vehicle?make=$(enc "$make")&model=$(enc "$model")&year=$year" 1
  [ -n "$group" ] || group=$(jq -r '.components[0].group.group_id // empty' <<<"$BODY")
  if [ -n "$group" ]; then
    check "/api/issue/$group?page=1&page_size=20" 1
  else
    echo "FAIL no group_id to request /api/issue (vehicle $make $model $year)"
    fails=$((fails + 1))
  fi
  echo "outage check: release ${RR_GIT_SHA:0:7} mode $RR_MODE vehicle '$make $model $year' -> $fails FAIL, $warns WARN"
  [ "$fails" = 0 ]
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
RELEASE=0
while [ $# -gt 0 ]; do
  case $1 in
    --release) RELEASE=1; shift ;;
    *) die "unknown argument $1 (usage: deploy/outage_check.sh [--release])" ;;
  esac
done
info "outage check on $RR_VM (release gate: $RELEASE)"
rr_run_on_vm "${BASH_SOURCE[0]}" "$RELEASE"
