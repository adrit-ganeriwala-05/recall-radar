#!/usr/bin/env bash
# Install the F9 messaging unit on the VM, DISABLED. Owner: D.
# Usage (laptop, repo root): bash deploy/messaging/install.sh [--yes]
# - copies the unit, creates /etc/recall-radar/messaging.env from the example only if it does not exist,
#   enables + (re)starts the unit, then runs deploy/messaging/health.sh on the VM.
# - never sets RR_MESSAGING_ENABLED=1, never installs the sidecar or the monitor timer, never touches Caddy.
# Needs a release that contains recall_radar/messaging (current symlink).
set -euo pipefail

on_vm() {
  local rel=/opt/recall-radar/current
  [ -f "$rel/recall_radar/messaging/app.py" ] || { echo "ERROR: $rel has no recall_radar/messaging (deploy a v2 release first)" >&2; exit 3; }
  install -d -m 755 /etc/recall-radar
  if [ ! -f /etc/recall-radar/messaging.env ]; then
    install -m 640 -o root -g rr "$rel/deploy/messaging/messaging.env.example" /etc/recall-radar/messaging.env
    echo "==> created /etc/recall-radar/messaging.env (RR_MESSAGING_ENABLED=0)"
  fi
  grep -qx 'RR_MESSAGING_ENABLED=0' /etc/recall-radar/messaging.env || echo "WARNING: messaging.env does not say RR_MESSAGING_ENABLED=0" >&2
  install -m 644 "$rel/deploy/messaging/recall-radar-messaging.service" /etc/systemd/system/recall-radar-messaging.service
  systemctl daemon-reload
  systemctl enable recall-radar-messaging >/dev/null 2>&1
  systemctl restart recall-radar-messaging
  bash "$rel/deploy/messaging/health.sh"
}

if [ "${1:-}" = --on-vm ]; then shift; on_vm "$@" </dev/null; exit; fi
# shellcheck source=deploy/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
[ "${1:-}" = --yes ] && RR_YES=1
rr_load_env
rr_confirm "Install the messaging unit (disabled) on $RR_VM?"
rr_run_on_vm "${BASH_SOURCE[0]}"
