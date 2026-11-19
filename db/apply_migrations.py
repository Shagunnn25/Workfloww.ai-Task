"""Applies every .sql file in db/migrations, in filename order, against DATABASE_URL.

Usage (from repo root): backend/.venv/bin/python db/apply_migrations.py
"""

import asyncio
import os
import pathlib
import sys

import asyncpg
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
MIGRATIONS_DIR = ROOT / "migrations"

load_dotenv(ROOT.parent / "backend" / ".env")


async def main() -> int:
    database_url = os.environ["DATABASE_URL"]
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 1

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        for path in files:
            print(f"Applying {path.name} ...")
            await conn.execute(path.read_text())
        print("All migrations applied.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
