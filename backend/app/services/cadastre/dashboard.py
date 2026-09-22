"""Dashboard statistics."""

from app import db
from app.services.cadastre import scene


async def stats() -> dict:
    conn = db.pool()
    return await scene._stats(conn)