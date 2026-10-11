#!/usr/bin/env bash
# F9 health check, run ON THE VM. Owner: D. Exit 0 only when the service answers and its state is as expected.
# Default expectation: disabled (enabled=false, webhook → 503). EXPECT=enabled for Gate P.
set -euo pipefail
expect=${EXPECT:-disabled}
for _ in $(seq 1 30); do body=$(curl -fsS -m 2 http://127.0.0.1:8791/healthz 2>/dev/null) && break; body=""; sleep 0.5; done
[ -n "$body" ] || { echo "FAIL messaging /healthz does not answer"; journalctl -u recall-radar-messaging -n 30 --no-pager; exit 1; }
code=$(curl -s -o /dev/null -w '%{http_code}' -m 5 -X POST -H 'content-type: application/json' --data '{}' http://127.0.0.1:8791/spectrum-webhook)
echo "messaging /healthz: $body · unsigned webhook → $code"
if [ "$expect" = disabled ]; then
  case $body in *'"enabled":false'*) ;; *) echo "FAIL expected enabled=false"; exit 1 ;; esac
  [ "$code" = 503 ] || { echo "FAIL expected 503 from the webhook while disabled"; exit 1; }
  [ ! -e /opt/recall-radar/data/messaging.sqlite ] && echo "ok: no messaging.sqlite (nothing stored)" || echo "note: messaging.sqlite exists (from an earlier enabled run)"
else
  case $body in *'"enabled":true'*) ;; *) echo "FAIL expected enabled=true"; exit 1 ;; esac
  [ "$code" = 401 ] || [ "$code" = 400 ] || { echo "FAIL an unsigned webhook must be rejected (got $code)"; exit 1; }
fi
systemctl is-active --quiet recall-radar-messaging && echo "PASS messaging $expect"
