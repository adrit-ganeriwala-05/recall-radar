#!/usr/bin/env bash
# Gate P switch (PRD_v2 §8). Owner: D. Usage (laptop): bash deploy/messaging/gatep.sh on|off|status [--yes]
#   on   RR_MESSAGING_ENABLED=1, start the sidecar, restart messaging, health EXPECT=enabled
#   off  RR_MESSAGING_ENABLED=0, stop the sidecar (outbound kill switch), restart messaging, health EXPECT=disabled
# Turn it on only for the Gate P run with the opted-in tester; turn it off right after.
set -euo pipefail

on_vm() {
  local mode=$1 f=/etc/recall-radar/messaging.env
  case $mode in
    on)
      sed -i 's/^RR_MESSAGING_ENABLED=.*/RR_MESSAGING_ENABLED=1/' "$f"
      systemctl start recall-radar-sidecar
      systemctl restart recall-radar-messaging
      EXPECT=enabled bash /opt/recall-radar/current/deploy/messaging/health.sh
      systemctl is-active recall-radar-sidecar | sed 's/^/sidecar: /' ;;
    off)
      sed -i 's/^RR_MESSAGING_ENABLED=.*/RR_MESSAGING_ENABLED=0/' "$f"
      systemctl stop recall-radar-sidecar || true
      systemctl restart recall-radar-messaging
      EXPECT=disabled bash /opt/recall-radar/current/deploy/messaging/health.sh
      systemctl is-active recall-radar-sidecar | sed 's/^/sidecar: /' || true ;;
    status)
      grep '^RR_MESSAGING_ENABLED=' "$f"
      for u in recall-radar-messaging recall-radar-sidecar; do printf '%s: %s\n' "$u" "$(systemctl is-active $u || true)"; done
      journalctl -u recall-radar-sidecar -n 15 --no-pager -o cat | grep -v -i secret || true ;;
    *) echo "usage: gatep.sh on|off|status" >&2; exit 2 ;;
  esac
}

if [ "${1:-}" = --on-vm ]; then shift; on_vm "$@" </dev/null; exit; fi
# shellcheck source=deploy/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
MODE=${1:?usage: gatep.sh on|off|status [--yes]}
[ "${2:-}" = --yes ] && RR_YES=1
rr_load_env
[ "$MODE" = status ] || rr_confirm "Gate P: turn messaging $MODE on $RR_VM?"
rr_run_on_vm "${BASH_SOURCE[0]}" "$MODE"
