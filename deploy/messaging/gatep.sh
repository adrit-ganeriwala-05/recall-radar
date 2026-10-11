#!/usr/bin/env bash
# Gate P switch (PRD_v2 §8). Owner: D. Usage (laptop): bash deploy/messaging/gatep.sh on|off|status [--yes]
#   on   RR_MESSAGING_ENABLED=1, allow messaging outbound HTTPS (Gemini, brain.py), start the sidecar, restart
#        messaging, install + start the monitor timer (F9.6 alerts), health EXPECT=enabled
#   off  RR_MESSAGING_ENABLED=0, stop the monitor timer and the sidecar (outbound kill switch), remove the outbound
#        allowance, restart messaging, health EXPECT=disabled
# Turn it on only for the Gate P run with the opted-in tester; turn it off right after.
set -euo pipefail

on_vm() {
  local mode=$1 f=/etc/recall-radar/messaging.env rel=/opt/recall-radar/current
  local out=/etc/systemd/system/recall-radar-messaging.service.d/20-gatep-outbound.conf
  case $mode in
    on)
      sed -i 's/^RR_MESSAGING_ENABLED=.*/RR_MESSAGING_ENABLED=1/' "$f"
      install -d "$(dirname "$out")"
      printf '[Service]\n# Gate P only (gatep.sh): Gemini needs outbound HTTPS. Removed by gatep.sh off.\nIPAddressDeny=\n' >"$out"
      install -m 644 "$rel/deploy/messaging/recall-radar-monitor.service" "$rel/deploy/messaging/recall-radar-monitor.timer" /etc/systemd/system/
      systemctl daemon-reload
      systemctl start recall-radar-sidecar
      systemctl restart recall-radar-messaging
      systemctl start recall-radar-monitor.timer
      EXPECT=enabled bash /opt/recall-radar/current/deploy/messaging/health.sh
      systemctl is-active recall-radar-sidecar | sed 's/^/sidecar: /' ;;
    off)
      sed -i 's/^RR_MESSAGING_ENABLED=.*/RR_MESSAGING_ENABLED=0/' "$f"
      systemctl stop recall-radar-monitor.timer recall-radar-monitor.service 2>/dev/null || true
      systemctl stop recall-radar-sidecar || true
      rm -f "$out"
      systemctl daemon-reload
      systemctl restart recall-radar-messaging
      EXPECT=disabled bash /opt/recall-radar/current/deploy/messaging/health.sh
      systemctl is-active recall-radar-sidecar | sed 's/^/sidecar: /' || true ;;
    status)
      grep '^RR_MESSAGING_ENABLED=' "$f"
      for u in recall-radar-messaging recall-radar-sidecar recall-radar-monitor.timer; do printf '%s: %s\n' "$u" "$(systemctl is-active $u || true)"; done
      [ -f "$out" ] && echo "outbound: allowed (Gate P)" || echo "outbound: loopback only"
      journalctl -u recall-radar-monitor -n 3 --no-pager -o cat || true
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
