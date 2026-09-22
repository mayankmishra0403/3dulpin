import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    """Create a reusable asyncpg connection pool for the PostGIS database."""
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised (call connect() first)")
    return _pool