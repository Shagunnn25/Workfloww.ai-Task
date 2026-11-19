import asyncpg

from app.core.config import settings


async def create_db_pool() -> asyncpg.Pool:
    """Create the asyncpg pool used against Supabase's transaction pooler.

    statement_cache_size=0 disables asyncpg's client-side prepared-statement
    cache. In transaction-pooling mode the pooler can hand out a different
    underlying server connection per transaction, so a statement prepared on
    one physical connection may not exist on the next -> caching must stay off.
    """
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        statement_cache_size=0,
    )
