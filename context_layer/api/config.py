"""Service configuration — env vars only, no hardcoded secrets, sensible
defaults that require nothing paid or external ("DEMO MODE" is the
default: no LLM key needed to start the service or hit any endpoint
except an explicit real-LLM request)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    app_env: str
    log_level: str
    host: str
    port: int
    data_mode: str  # "synthetic" (only mode this prototype supports — documented, not silently ignored)
    eval_mode: str  # "fast" | "llm" | "full" — default "fast" needs no credentials


def get_service_config() -> ServiceConfig:
    return ServiceConfig(
        app_env=os.environ.get("APP_ENV", "demo"),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8080")),
        data_mode=os.environ.get("DATA_MODE", "synthetic"),
        eval_mode=os.environ.get("EVAL_MODE", "fast"),
    )
