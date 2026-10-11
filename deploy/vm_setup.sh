#!/usr/bin/env bash
# One-time, idempotent VM preparation (Vultr Ubuntu 24.04, 2 vCPU / 4 GB). Owner: D.
# Run from the repo root on the laptop:   bash deploy/vm_setup.sh [--site <domain|:80>] [--yes]
# (make vm-setup). It copies the Caddyfile and unit file to the VM, then as root installs
# caddy rsync curl jq ufw make, uv in /usr/local/bin, system user `rr`,
# /opt/recall-radar/{releases,data}, the Caddy site (RR_SITE: domain -> HTTPS, :80 -> HTTP),
# enables recall-radar.service (the first deploy starts it) and opens ufw for 22/80/443 only.
# Credentials never pass through this script: SSH uses your key (BatchMode, no passwords).
set -euo pipefail

on_vm() {
  local stage=$1 site=$2
  [ "$(id -u)" = 0 ] || { echo "vm_setup must run as root" >&2; exit 1; }
  # shellcheck disable=SC1091
  . /etc/os-release
  [ "$ID" = ubuntu ] || echo "WARN: written for Ubuntu 24.04; this is $PRETTY_NAME" >&2
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -q
  apt-get install -y -q ca-certificates curl rsync jq ufw make
  if ! apt-get install -y -q caddy; then
    echo "caddy not in the Ubuntu archive here; using Caddy's official apt repository"
    apt-get install -y -q debian-keyring debian-archive-keyring apt-transport-https gnupg
    curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key |
      gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
      >/etc/apt/sources.list.d/caddy-stable.list
    apt-get update -q
    apt-get install -y -q caddy
  fi
  if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh
  fi
  id rr >/dev/null 2>&1 || useradd --system --create-home --home-dir /home/rr --shell /usr/sbin/nologin rr
  install -d -o rr -g rr -m 755 /opt/recall-radar /opt/recall-radar/releases /opt/recall-radar/data

  install -m 644 "$stage/Caddyfile" /etc/caddy/Caddyfile
  install -d /etc/systemd/system/caddy.service.d
  # quoted: a site list such as "example.org, www.example.org, :80" contains spaces
  printf '[Service]\nEnvironment="RR_SITE=%s"\n' "$site" >/etc/systemd/system/caddy.service.d/recall-radar.conf
  install -m 644 "$stage/recall-radar.service" /etc/systemd/system/recall-radar.service
  systemctl daemon-reload
  RR_SITE="$site" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
  systemctl enable caddy
  systemctl restart caddy
  systemctl enable recall-radar

  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
  rm -rf -- "$stage"

  echo "--- summary"
  echo "caddy $(caddy version | cut -d' ' -f1) site=$site | $(uv --version) | user rr: $(id rr)"
  ufw status | sed -n '1,8p'
  echo "vm_setup done. Next: bash deploy/deploy.sh <ref> --mode fixture"
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
SITE=""
while [ $# -gt 0 ]; do
  case $1 in
    --site) SITE=${2:?--site needs a value}; shift 2 ;;
    --yes | -y) RR_YES=1; shift ;;
    *) die "unknown argument: $1 (usage: deploy/vm_setup.sh [--site <domain|:80>] [--yes])" ;;
  esac
done
SITE=${SITE:-${RR_SITE:-:80}}
rr_confirm "Prepare $RR_VM for Recall Radar (Caddy site '$SITE', ufw 22/80/443)?"
STAGE=/tmp/rr-setup
rr_ssh "$RR_SUDO install -d -m 700 $STAGE"
rr_rsync "$RR_ROOT/deploy/Caddyfile" "$RR_ROOT/deploy/recall-radar.service" "$RR_VM:$STAGE/"
rr_run_on_vm "${BASH_SOURCE[0]}" "$STAGE" "$SITE"
