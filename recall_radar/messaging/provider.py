"""Outbound adapter. Photon's runtime send is SDK-only (TypeScript), so production goes through the small
sidecar in `photon_ts/` over HTTP; tests use MockProvider. A timeout is 'uncertain' and is never resent blindly."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class SendResult:
    status: Literal["accepted", "failed", "uncertain"]
    provider_message_id: str | None = None
    detail: str = ""


class Provider(Protocol):
    def send(self, route: str, text: str, idempotency_key: str) -> SendResult: ...


@dataclass
class MockProvider:
    script: list[SendResult] = field(default_factory=list)  # results to return in order; default accepted
    sent: list[tuple[str, str, str]] = field(default_factory=list)

    def send(self, route: str, text: str, idempotency_key: str) -> SendResult:
        self.sent.append((route, text, idempotency_key))
        return self.script.pop(0) if self.script else SendResult("accepted", f"msg-{len(self.sent)}")


@dataclass
class SidecarProvider:
    url: str = field(default_factory=lambda: os.environ.get("RR_PHOTON_SIDECAR_URL", "http://127.0.0.1:8790"))
    timeout_s: float = 15

    def send(self, route: str, text: str, idempotency_key: str) -> SendResult:
        req = urllib.request.Request(
            f"{self.url}/send", method="POST", headers={"content-type": "application/json"},
            data=json.dumps({"space": route, "text": text, "idempotencyKey": idempotency_key}).encode())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                body = json.loads(r.read() or b"{}")
                return SendResult("accepted", body.get("messageId"))
        except urllib.error.HTTPError as e:
            return SendResult("failed" if e.code < 500 else "uncertain", detail=f"HTTP {e.code}")
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            return SendResult("uncertain", detail=str(e)[:200])
