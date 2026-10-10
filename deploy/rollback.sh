#!/usr/bin/env bash
# Switch the VM back to an earlier release without rebuilding. Owner: D.
# Usage: bash deploy/rollback.sh [<sha-prefix>] [--yes]       (make rollback [REF=<sha-prefix>])
# No argument: swap `current` and `previous`. With a SHA prefix: switch to that release
# directory if it is still on the VM (deploy.sh keeps the 5 newest). Each release carries its own
# .deploy.env, so the mode (cached|fixture) comes back with it. To redeploy a tag that is no
# longer on the VM, use: make deploy REF=<lkg tag>.
set -euo pipefail

on_vm() {
  local want=${1:-} app=/opt/recall-radar cur new matches body=""
  cur=$(readlink -f "$app/current" 2>/dev/null || true)
  if [ -n "$want" ]; then
    matches=("$app"/releases/"$want"*/)
    [ "${#matches[@]}" = 1 ] && [ -d "${matches[0]}" ] || { echo "ERROR: need exactly one release matching '$want'" >&2; ls -1t "$app/releases" >&2; exit 1; }
    new=${matches[0]%/}
  else
    new=$(readlink -f "$app/previous" 2>/dev/null || true)
    [ -n "$new" ] && [ -d "$new" ] || { echo "ERROR: no previous release recorded" >&2; exit 1; }
  fi
  [ "$new" != "$cur" ] || { echo "ERROR: $(basename "$new") is already current" >&2; exit 1; }
  ln -sfn "$new" "$app/current.new" && mv -Tf "$app/current.new" "$app/current"
  if [ -n "$cur" ]; then ln -sfn "$cur" "$app/previous.new" && mv -Tf "$app/previous.new" "$app/previous"; fi
  systemctl restart recall-radar
  for _ in $(seq 1 60); do
    if body=$(curl -fsS -m 2 http://127.0.0.1:8000/healthz 2>/dev/null); then break; fi
    body=""
    sleep 0.5
  done
  [ -n "$body" ] || { journalctl -u recall-radar -n 40 --no-pager >&2; echo "ERROR: $(basename "$new") is not healthy" >&2; exit 1; }
  echo "$(date -u +%FT%TZ) rollback $(basename "$new") from $(basename "${cur:-none}")" >>"$app/DEPLOYS.log"
  echo "now current: $(basename "$new") ; previous: $(basename "${cur:-none}")"
  echo "VM /healthz: $body"
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
WANT=""
while [ $# -gt 0 ]; do
  case $1 in
    --yes | -y) RR_YES=1; shift ;;
    -*) die "unknown option $1 (usage: deploy/rollback.sh [<sha-prefix>] [--yes])" ;;
    *) WANT=$1; shift ;;
  esac
done
rr_confirm "Roll $RR_VM back to ${WANT:-the previous release}?"
rr_run_on_vm "${BASH_SOURCE[0]}" "$WANT"
info "public check: $(curl -fsS -m 15 "$RR_PUBLIC_BASE_URL/healthz" || echo 'public URL not answering')"
