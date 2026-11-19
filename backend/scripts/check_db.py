"""Standalone DB connectivity check.

Run from /backend with: python -m scripts.check_db
Connects directly (bypassing FastAPI), prints the Postgres version and the
current role, and exits non-zero on failure so it's CI/script friendly.
"""

import asyncio
import sys

import asyncpg

from app.core.config import settings


async def main() -> int:
    try:
        conn = await asyncpg.connect(dsn=settings.database_url, statement_cache_size=0)
    except Exception as exc:
        print(f"FAILED to connect: {exc}")
        return 1

    try:
        version = await conn.fetchval("SELECT version()")
        role = await conn.fetchval("SELECT current_user")
        print("Connected OK")
        print(f"Postgres version: {version}")
        print(f"Current role: {role}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
