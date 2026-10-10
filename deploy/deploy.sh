#!/usr/bin/env bash
# Release a git ref to the VM. Owner: D.
# Usage: bash deploy/deploy.sh <ref> [--mode cached|fixture] [--yes] [--build-only]
#        make deploy REF=<ref> MODE=<cached|fixture>
# 1. git archive <ref> (committed files only) into a temp dir; write REVISION and .deploy.env
#    (RR_MODE, RR_GIT_SHA). 2. npm ci + build web/dist with VITE_API_MODE=live; fail on any
#    secret-like string in the bundle. 3. rsync to /opt/recall-radar/releases/<sha>.
# 4. On the VM: uv sync --locked --no-dev as user rr; refresh the unit file and Caddyfile if they
#    changed; switch `current` (the old target becomes `previous`); restart; wait for /healthz.
#    If the new release is unhealthy the previous one is restored automatically.
# 5. Print /healthz from the public URL and compare its git_sha with the deployed SHA.
# --build-only stops after step 2 and keeps the build directory (no VM needed).
set -euo pipefail

on_vm() {
  local sha=$1 mode=$2 app=/opt/recall-radar
  local rel=$app/releases/$sha prev
  [ -d "$rel" ] || { echo "ERROR: $rel was not uploaded" >&2; exit 1; }
  chown -R rr:rr "$rel"
  echo "==> uv sync --locked --no-dev (user rr)"
  (cd "$rel" && runuser -u rr -- env HOME=/home/rr /usr/local/bin/uv sync --locked --no-dev --quiet)
  if [ "$mode" = cached ] && [ ! -s "$app/data/recall_radar.duckdb" ]; then
    echo "ERROR: $app/data/recall_radar.duckdb is missing: run deploy/sync_data.sh first, or deploy --mode fixture" >&2
    exit 3
  fi
  if ! cmp -s "$rel/deploy/recall-radar.service" /etc/systemd/system/recall-radar.service; then
    install -m 644 "$rel/deploy/recall-radar.service" /etc/systemd/system/recall-radar.service
    systemctl daemon-reload
    echo "==> unit file updated"
  fi
  if ! cmp -s "$rel/deploy/Caddyfile" /etc/caddy/Caddyfile; then
    install -m 644 "$rel/deploy/Caddyfile" /etc/caddy/Caddyfile
    systemctl reload caddy
    echo "==> Caddyfile updated"
  fi

  prev=$(readlink -f "$app/current" 2>/dev/null || true)
  ln -sfn "$rel" "$app/current.new" && mv -Tf "$app/current.new" "$app/current"
  if [ -n "$prev" ] && [ "$prev" != "$rel" ]; then
    ln -sfn "$prev" "$app/previous.new" && mv -Tf "$app/previous.new" "$app/previous"
  fi
  systemctl restart recall-radar

  local body=""
  for _ in $(seq 1 60); do
    if body=$(curl -fsS -m 2 http://127.0.0.1:8000/healthz 2>/dev/null); then break; fi
    body=""
    sleep 0.5
  done
  if [ -z "$body" ]; then
    echo "ERROR: release ${sha:0:7} did not answer /healthz within 30 s" >&2
    journalctl -u recall-radar -n 40 --no-pager >&2 || true
    if [ -n "$prev" ] && [ "$prev" != "$rel" ]; then
      ln -sfn "$prev" "$app/current.new" && mv -Tf "$app/current.new" "$app/current"
      systemctl restart recall-radar
      echo "ROLLED BACK to $(basename "$prev")" >&2
    fi
    exit 1
  fi
  echo "$(date -u +%FT%TZ) deploy $sha $mode" >>"$app/DEPLOYS.log"
  # keep the 5 newest releases plus whatever current/previous point to
  local cur keep_prev d
  cur=$(readlink -f "$app/current")
  keep_prev=$(readlink -f "$app/previous" 2>/dev/null || true)
  while read -r d; do
    d=${d%/}
    [ "$d" = "$cur" ] || [ "$d" = "$keep_prev" ] || rm -rf -- "$d"
  done < <(ls -1dt "$app"/releases/*/ | tail -n +6)
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
REF="" MODE=${RR_DEPLOY_MODE:-cached} BUILD_ONLY=0
while [ $# -gt 0 ]; do
  case $1 in
    --mode) MODE=${2:?--mode needs cached or fixture}; shift 2 ;;
    --yes | -y) RR_YES=1; shift ;;
    --build-only) BUILD_ONLY=1; shift ;;
    -*) die "unknown option $1 (usage: deploy/deploy.sh <ref> [--mode cached|fixture] [--yes] [--build-only])" ;;
    *) REF=$1; shift ;;
  esac
done
REF=${REF:-HEAD}
case $MODE in cached | fixture) ;; *) die "--mode must be cached or fixture, not '$MODE'" ;; esac
SHA=$(git -C "$RR_ROOT" rev-parse --verify --quiet "$REF^{commit}") || die "unknown git ref '$REF'"
SHORT=${SHA:0:7}

if [ "$BUILD_ONLY" = 0 ]; then
  rr_load_env
  git -C "$RR_ROOT" fetch -q origin 2>/dev/null || warn "git fetch failed; cannot check origin/main"
  if ! git -C "$RR_ROOT" merge-base --is-ancestor "$SHA" origin/main 2>/dev/null; then
    warn "$REF ($SHORT) is not on origin/main: fine for a fixture or trial deploy, never for a release"
  fi
  rr_confirm "Deploy $SHORT ($REF, mode $MODE) to $RR_VM ($RR_PUBLIC_BASE_URL)?"
fi

BUILD=$(mktemp -d "${TMPDIR:-/tmp}/rr-release-XXXXXX")
[ "$BUILD_ONLY" = 1 ] || trap 'rm -rf -- "$BUILD"' EXIT
info "packaging $SHORT into $BUILD"
git -C "$RR_ROOT" archive --format=tar "$SHA" | tar -x -C "$BUILD"
printf '%s\n' "$SHA" >"$BUILD/REVISION"
printf 'RR_MODE=%s\nRR_GIT_SHA=%s\n' "$MODE" "$SHA" >"$BUILD/.deploy.env"
if [ -f "$BUILD/web/package-lock.json" ]; then
  info "building web/dist (npm ci + build, VITE_API_MODE=live)"
  npm --prefix "$BUILD/web" ci --no-audit --no-fund --loglevel=error
  VITE_API_MODE=live npm --prefix "$BUILD/web" run build
  rm -rf -- "$BUILD/web/node_modules"
  [ -f "$BUILD/web/dist/index.html" ] || die "web build produced no web/dist/index.html"
  if grep -rEln "AIza[0-9A-Za-z_-]{35}|sk-ant-|GEMINI_API_KEY|RR_VM_" "$BUILD/web/dist"; then
    die "secret-like string in web/dist (files above); not deploying"
  fi
else
  warn "no web/package-lock.json at $SHORT: releasing the API only (no UI)"
fi
info "release size $(du -sh "$BUILD" | cut -f1)"
if [ "$BUILD_ONLY" = 1 ]; then
  info "build only: $BUILD (delete it when done)"
  exit 0
fi

info "uploading $SHORT to $RR_VM:$RR_APP_DIR/releases/$SHA"
rr_ssh "$RR_SUDO install -d -o rr -g rr $RR_APP_DIR/releases/$SHA"
rr_rsync --delete --exclude /.venv/ "$BUILD/" "$RR_VM:$RR_APP_DIR/releases/$SHA/"
rr_run_on_vm "${BASH_SOURCE[0]}" "$SHA" "$MODE"

info "public check: $RR_PUBLIC_BASE_URL/healthz"
BODY=$(curl -fsS -m 15 "$RR_PUBLIC_BASE_URL/healthz") ||
  die "public URL does not answer (Caddy, DNS or ufw?); the VM itself is healthy, see above"
echo "$BODY"
case $BODY in
  *"\"$SHA\""* | *"\"$SHORT"*) info "deployed $SHORT ($MODE) at $RR_PUBLIC_BASE_URL" ;;
  *) warn "/healthz git_sha is not $SHORT: the API must report RR_GIT_SHA (docs/handoffs D-to-A healthz request)" ;;
esac
