"""Lightweight, prototype-appropriate observability — Phase 10. One JSON
line per request to stdout (container-friendly, no file management), a
generated request_id threaded through the response and every log line
for correlation, and latency. Never logs secrets, API keys, or a raw
exception traceback — those go to the server-side logger's `exc_info`
only, keyed by request_id, never into the HTTP response body.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass

logger = logging.getLogger("context_layer.api")


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False


def new_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:16]}"


@dataclass
class RequestLogEntry:
    request_id: str
    method: str
    path: str
    status_code: int | None = None
    latency_ms: float | None = None
    agent_id: str | None = None
    entity_id: str | None = None
    purpose: str | None = None
    allowed_domains: list[str] | None = None
    context_package_id: str | None = None
    error: str | None = None


def log_request(entry: RequestLogEntry) -> None:
    logger.info(json.dumps({"event": "request", **{k: v for k, v in asdict(entry).items() if v is not None}}))


@contextmanager
def timed_request(method: str, path: str, request_id: str):
    entry = RequestLogEntry(request_id=request_id, method=method, path=path)
    start = time.perf_counter()
    try:
        yield entry
    except Exception as exc:  # noqa: BLE001 - always logged, then re-raised for the HTTP layer to shape a safe response
        entry.error = type(exc).__name__
        logger.error(json.dumps({"event": "request_error", "request_id": request_id, "error": str(exc)}), exc_info=True)
        raise
    finally:
        entry.latency_ms = round((time.perf_counter() - start) * 1000, 3)
        log_request(entry)
