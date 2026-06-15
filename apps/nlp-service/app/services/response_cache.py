"""Redis-backed response cache for high-latency draft endpoints.

Designed to degrade gracefully: if Redis is disabled via config or
unreachable at runtime, ``get`` returns ``None`` and ``set`` is a no-op,
so the caller always computes a fresh response. Short socket timeouts
keep a flaky Redis from slowing requests below the no-cache baseline.
"""

from __future__ import annotations

import hashlib
from typing import Any

import orjson
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger("nlp.cache")

# Keep Redis from ever blocking a request for long. Cache is best-effort.
_SOCKET_TIMEOUT_S = 0.25


class ResponseCache:
    """Thin async wrapper around a Redis connection.

    Use ``ResponseCache.connect()`` for a live cache or
    ``ResponseCache.disabled()`` for a no-op instance.
    """

    def __init__(self, client: Any | None, *, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    @classmethod
    def disabled(cls) -> "ResponseCache":
        return cls(client=None, ttl_seconds=0)

    @classmethod
    def connect(cls, url: str, *, ttl_seconds: int) -> "ResponseCache":
        # Import lazily so the dep is only required when caching is enabled.
        from redis.asyncio import Redis

        client = Redis.from_url(
            url,
            socket_timeout=_SOCKET_TIMEOUT_S,
            socket_connect_timeout=_SOCKET_TIMEOUT_S,
            decode_responses=False,
        )
        logger.info(
            "cache.enabled",
            extra={"extras": {"url": url, "ttl_seconds": ttl_seconds}},
        )
        return cls(client=client, ttl_seconds=ttl_seconds)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def with_ttl(self, ttl_seconds: int) -> "ResponseCache":
        """Return a cache sharing this instance's connection with a different TTL.

        Lets multiple endpoints share one Redis connection while using
        different expiry policies (e.g. short-TTL `/rhymes` vs. long-TTL
        `/analyze-draft`). Only one of the resulting instances needs closing.
        """
        return ResponseCache(client=self._client, ttl_seconds=ttl_seconds)

    @staticmethod
    def make_key(namespace: str, payload: BaseModel) -> str:
        """Content-addressed key: sha256 of canonical JSON-dumped payload."""
        body = orjson.dumps(
            payload.model_dump(mode="json"), option=orjson.OPT_SORT_KEYS
        )
        digest = hashlib.sha256(body).hexdigest()
        return f"{namespace}:{digest}"

    async def get(self, key: str) -> dict | None:
        if self._client is None:
            return None
        try:
            raw = await self._client.get(key)
        except Exception as exc:
            logger.warning(
                "cache.get_failed",
                extra={"extras": {"key": key, "error": repr(exc)}},
            )
            return None
        if raw is None:
            return None
        try:
            return orjson.loads(raw)
        except orjson.JSONDecodeError:
            logger.warning("cache.decode_failed", extra={"extras": {"key": key}})
            return None

    async def set(self, key: str, value: dict) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key, orjson.dumps(value), ex=self._ttl)
        except Exception as exc:
            logger.warning(
                "cache.set_failed",
                extra={"extras": {"key": key, "error": repr(exc)}},
            )

    async def close(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.aclose()
        except Exception:
            pass
