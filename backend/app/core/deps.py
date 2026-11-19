import json
from dataclasses import dataclass
from uuid import UUID

import asyncpg
from fastapi import HTTPException, Request, status

from app.core.security import decode_access_token, extract_bearer_token


@dataclass
class Caller:
    id: UUID
    company_id: UUID
    role: str
    full_name: str
    email: str


@dataclass
class RequestContext:
    conn: asyncpg.Connection
    caller: Caller


async def get_request_context(request: Request):
    """Per-request DB transaction, scoped to the caller's identity.

    Identity comes only from the verified JWT -- never from the request
    body or query params. Inside this one transaction we switch to the
    `authenticated` Postgres role and set `request.jwt.claims`, so the RLS
    policies defined in the database (not just this code) enforce
    company/row isolation. The pool's own role bypasses RLS, so user-facing
    queries must never run on it directly.
    """
    token = extract_bearer_token(request)
    claims = decode_access_token(token)
    user_id = claims["sub"]

    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE authenticated")
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"sub": user_id, "role": "authenticated"}),
            )

            row = await conn.fetchrow(
                "SELECT id, company_id, role, full_name, email FROM public.users WHERE id = $1",
                user_id,
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No profile for this account")

            yield RequestContext(conn=conn, caller=Caller(**dict(row)))
