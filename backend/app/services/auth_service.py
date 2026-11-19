import json

import asyncpg
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_SUPABASE_TIMEOUT = 10.0


async def login(pool: asyncpg.Pool, email: str, password: str) -> dict:
    async with httpx.AsyncClient(timeout=_SUPABASE_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )

    if resp.status_code != 200:
        # Don't pass Supabase's own error body through to the client.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    data = resp.json()
    access_token = data["access_token"]
    user_id = data["user"]["id"]

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL ROLE authenticated")
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"sub": user_id, "role": "authenticated"}),
            )
            profile = await conn.fetchrow("SELECT role, full_name FROM public.users WHERE id = $1", user_id)

    if profile is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No profile for this account")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": profile["role"],
        "full_name": profile["full_name"],
    }
