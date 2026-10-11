"""Inbound webhook checks, per Photon Spectrum Stable docs: HMAC-SHA256 over `v0:<timestamp>:<raw body>`,
header `X-Spectrum-Signature: v0=<hex>`, `X-Spectrum-Timestamp` within 5 minutes, dedupe by `X-Spectrum-Webhook-Id`."""

from __future__ import annotations

import hashlib
import hmac
import time

MAX_BODY = 64 * 1024
WINDOW_S = 300


class Rejected(Exception):
    def __init__(self, status: int, reason: str):
        super().__init__(reason)
        self.status, self.reason = status, reason


def sign(secret: str, timestamp: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), b"v0:" + timestamp.encode() + b":" + body, hashlib.sha256).hexdigest()
    return f"v0={mac}"


def verify(secret: str, headers: dict[str, str], body: bytes, now: float | None = None) -> None:
    """Raise Rejected(400|401|413) unless the delivery is authentic, fresh and small."""
    if not secret:
        raise Rejected(401, "no signing secret configured")
    if len(body) > MAX_BODY:
        raise Rejected(413, "body too large")
    h = {k.lower(): v for k, v in headers.items()}
    sig, ts = h.get("x-spectrum-signature"), h.get("x-spectrum-timestamp")
    if not sig or not ts:
        raise Rejected(400, "missing signature headers")
    try:
        age = abs((now if now is not None else time.time()) - int(ts))
    except ValueError as e:
        raise Rejected(400, "bad timestamp") from e
    if age > WINDOW_S:
        raise Rejected(401, "stale timestamp")
    if not hmac.compare_digest(sign(secret, ts, body), sig):
        raise Rejected(401, "bad signature")
