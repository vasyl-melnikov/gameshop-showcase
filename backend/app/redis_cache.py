from typing import AsyncGenerator

from redis import asyncio as aioredis

from app.settings import settings

redis: aioredis.Redis | None = None


async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    global redis

    if redis is None:
        redis = aioredis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password
        )
    yield redis
