import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any

from app.core.config import settings


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = getattr(record, "extras", None)
        if isinstance(extras, dict):
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_nlp_configured", False):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
    root._nlp_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


@contextmanager
def timed(logger: logging.Logger, event: str, **fields: Any):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.info(event, extra={"extras": {**fields, "elapsed_ms": round(elapsed_ms, 2)}})
