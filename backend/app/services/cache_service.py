import json
from typing import Any

import redis.asyncio as redis

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    def __init__(self, redis_url: str, ttl: int = 300):
        self.redis_url = redis_url
        self.ttl = ttl
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        try:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            logger.info("redis_connected")
        except Exception as exc:
            logger.warning("redis_unavailable", error=str(exc))
            self._client = None

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()

    async def get(self, key: str) -> Any | None:
        if not self._client:
            return None
        try:
            value = await self._client.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            logger.warning("cache_get_error", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self._client:
            return
        try:
            await self._client.setex(key, ttl or self.ttl, json.dumps(value))
        except Exception as exc:
            logger.warning("cache_set_error", key=key, error=str(exc))

    async def delete(self, key: str) -> None:
        if not self._client:
            return
        try:
            await self._client.delete(key)
        except Exception as exc:
            logger.warning("cache_delete_error", key=key, error=str(exc))

    def cache_key(self, prefix: str, *parts: str) -> str:
        return f"{prefix}:{':'.join(parts)}"
