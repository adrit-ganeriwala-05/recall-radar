#!/usr/bin/env bash
# Install the F9 Photon sidecar on the VM — installed, NOT started. Owner: D.
# Usage (laptop, repo root): bash deploy/messaging/sidecar-install.sh [--yes]
# Reads ~/.config/recall-radar/photon.env (PROJECT_ID, PROJECT_SECRET, IMESSAGE_WEBHOOK_SECRET) on the laptop and
# writes, without printing them: /etc/recall-radar/photon.env (PROJECT_ID, PROJECT_SECRET; root:rr 0640) and the
# webhook secret into /etc/recall-radar/messaging.env (RR_MESSAGING_ENABLED is left as it is, 0 by default).
# Installs Node 22 LTS from nodejs.org (SHA-256 checked against SHASUMS256.txt), `npm ci` of the pinned runtime in
# /opt/recall-radar/sidecar, copies sidecar.ts from the current release, installs the unit. Needs a v2 release.
set -euo pipefail

on_vm() {
  local rel=/opt/recall-radar/current dst=/opt/recall-radar/sidecar
  [ -f "$rel/recall_radar/messaging/photon_ts/sidecar.ts" ] || { echo "ERROR: deploy a v2 release first" >&2; exit 3; }
  if ! /usr/local/bin/node --version 2>/dev/null | grep -q '^v22\.'; then
    local ver tmp
    ver=$(curl -fsSL https://nodejs.org/dist/index.json | jq -r '[.[] | select(.version|startswith("v22.")) | select(.lts)][0].version')
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/node.tar.xz" "https://nodejs.org/dist/$ver/node-$ver-linux-x64.tar.xz"
    curl -fsSL -o "$tmp/SHASUMS256.txt" "https://nodejs.org/dist/$ver/SHASUMS256.txt"
    (cd "$tmp" && grep " node-$ver-linux-x64.tar.xz\$" SHASUMS256.txt | sed "s| node-$ver-linux-x64.tar.xz| node.tar.xz|" | sha256sum -c -)
    install -d /usr/local/lib/nodejs
    tar -xJf "$tmp/node.tar.xz" -C /usr/local/lib/nodejs
    for b in node npm npx; do ln -sfn "/usr/local/lib/nodejs/node-$ver-linux-x64/bin/$b" "/usr/local/bin/$b"; done
    rm -rf "$tmp"
  fi
  echo "==> node $(/usr/local/bin/node --version)"
  install -d -o rr -g rr -m 755 "$dst"
  install -o rr -g rr -m 644 "$rel/deploy/messaging/sidecar/package.json" "$rel/deploy/messaging/sidecar/package-lock.json" "$dst/"
  install -o rr -g rr -m 644 "$rel/recall_radar/messaging/photon_ts/sidecar.ts" "$dst/sidecar.ts"
  (cd "$dst" && runuser -u rr -- env HOME=/home/rr PATH=/usr/local/bin:/usr/bin:/bin npm ci --omit=dev --no-audit --no-fund --loglevel=error)
  install -d -m 755 /etc/recall-radar
  [ -s /tmp/rr-photon.env ] || { echo "ERROR: secrets were not uploaded" >&2; exit 4; }
  grep -E '^(PROJECT_ID|PROJECT_SECRET)=' /tmp/rr-photon.env >/etc/recall-radar/photon.env
  chown root:rr /etc/recall-radar/photon.env && chmod 640 /etc/recall-radar/photon.env
  [ -f /etc/recall-radar/messaging.env ] || install -m 640 -o root -g rr "$rel/deploy/messaging/messaging.env.example" /etc/recall-radar/messaging.env
  local secret
  secret=$(sed -n 's/^IMESSAGE_WEBHOOK_SECRET=//p' /tmp/rr-photon.env)
  sed -i '/^IMESSAGE_WEBHOOK_SECRET=/d' /etc/recall-radar/messaging.env
  printf 'IMESSAGE_WEBHOOK_SECRET=%s\n' "$secret" >>/etc/recall-radar/messaging.env
  chown root:rr /etc/recall-radar/messaging.env && chmod 640 /etc/recall-radar/messaging.env
  shred -u /tmp/rr-photon.env 2>/dev/null || rm -f /tmp/rr-photon.env
  install -m 644 "$rel/deploy/messaging/recall-radar-sidecar.service" /etc/systemd/system/recall-radar-sidecar.service
  systemctl daemon-reload
  systemctl stop recall-radar-sidecar 2>/dev/null || true
  echo "==> sidecar installed, stopped (start only with deploy/messaging/gatep.sh on)"
  grep -c '^PROJECT_' /etc/recall-radar/photon.env | sed 's/^/photon.env keys: /'
  grep -q '^IMESSAGE_WEBHOOK_SECRET=.\+' /etc/recall-radar/messaging.env && echo "messaging.env: webhook secret set"
  grep '^RR_MESSAGING_ENABLED=' /etc/recall-radar/messaging.env
}

if [ "${1:-}" = --on-vm ]; then shift; on_vm "$@" </dev/null; exit; fi
# shellcheck source=deploy/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
[ "${1:-}" = --yes ] && RR_YES=1
SECRETS="$HOME/.config/recall-radar/photon.env"
for k in PROJECT_ID PROJECT_SECRET IMESSAGE_WEBHOOK_SECRET; do
  grep -q "^$k=.\+" "$SECRETS" || die "$k is empty in $SECRETS"
done
rr_load_env
rr_confirm "Install the Photon sidecar (stopped) on $RR_VM and upload the Photon secrets?"
rr_ssh "umask 077 && cat > /tmp/rr-photon.env" <"$SECRETS"
rr_run_on_vm "${BASH_SOURCE[0]}"
