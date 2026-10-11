# shellcheck shell=bash disable=SC2034  # variables here are used by the scripts that source it
# Shared laptop-side helpers for deploy/*.sh. Owner: D. Sourced, never run directly.
#
# Settings come from the environment or, if unset there, from .env at the repo root. Only these
# keys are read from .env (secrets such as GEMINI_API_KEY are never loaded):
#   RR_VM_HOST          VM IP or domain (required)
#   RR_VM_USER          SSH user (default root; a non-root user needs passwordless sudo)
#   RR_PUBLIC_BASE_URL  public URL (default http://$RR_VM_HOST)
#   RR_SITE             Caddy site address: a domain name (automatic HTTPS) or :80 (default)
# Unfilled placeholders copied from env.example (values containing <...>) count as unset.

RR_APP_DIR=/opt/recall-radar
RR_SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)

die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
info() { printf '==> %s\n' "$*"; }
warn() { printf 'WARN: %s\n' "$*" >&2; }

RR_ROOT=$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)

# rr_env_get KEY -> value from the environment, else the last KEY= line of .env, else empty.
rr_env_get() {
  local key=$1 val=${!1:-}
  if [ -z "$val" ] && [ -f "$RR_ROOT/.env" ]; then
    val=$(sed -n "s/^${key}=//p" "$RR_ROOT/.env" | tail -n 1 |
      sed -e 's/[[:space:]]#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
          -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/")
  fi
  case $val in *'<'*'>'*) val="" ;; esac
  printf '%s' "$val"
}

# rr_load_env: sets RR_VM_HOST RR_VM_USER RR_VM RR_SUDO RR_PUBLIC_BASE_URL RR_SITE.
rr_load_env() {
  RR_VM_HOST=$(rr_env_get RR_VM_HOST)
  RR_VM_USER=$(rr_env_get RR_VM_USER)
  RR_VM_USER=${RR_VM_USER:-root}
  RR_PUBLIC_BASE_URL=$(rr_env_get RR_PUBLIC_BASE_URL)
  RR_SITE=$(rr_env_get RR_SITE)
  [ -n "$RR_VM_HOST" ] || die "RR_VM_HOST is not set: put the VM IP or domain in .env (deploy/README.md)"
  RR_VM="$RR_VM_USER@$RR_VM_HOST"
  RR_PUBLIC_BASE_URL=${RR_PUBLIC_BASE_URL:-http://$RR_VM_HOST}
  RR_PUBLIC_BASE_URL=${RR_PUBLIC_BASE_URL%/}
  if [ "$RR_VM_USER" = root ]; then RR_SUDO=""; else RR_SUDO="sudo"; fi
}

rr_ssh() { ssh "${RR_SSH_OPTS[@]}" "$RR_VM" "$@"; }

# rr_rsync SRC... DEST — compressed, as root on the VM (via sudo for a non-root user).
rr_rsync() {
  local args=(-az -e "ssh ${RR_SSH_OPTS[*]}")
  [ -z "$RR_SUDO" ] || args+=(--rsync-path="sudo rsync")
  rsync "${args[@]}" "$@"
}

# rr_run_on_vm SCRIPT ARGS... — runs SCRIPT's on_vm() as root on the VM (script read from stdin).
rr_run_on_vm() {
  local script=$1
  shift
  rr_ssh "$RR_SUDO bash -s -- --on-vm $(printf '%q ' "$@")" <"$script"
}

# rr_confirm QUESTION — asks y/N; RR_YES=1 (or a script's --yes) skips the question.
rr_confirm() {
  [ "${RR_YES:-0}" = 1 ] && return 0
  [ -t 0 ] || die "no terminal to confirm '$1': re-run with --yes (or RR_YES=1)"
  local ans
  read -r -p "$1 [y/N] " ans
  case $ans in [yY] | [yY][eE][sS]) ;; *) die "aborted" ;; esac
}
