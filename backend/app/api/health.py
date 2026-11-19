from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    """Reports API status plus a real DB round-trip (SELECT 1)."""
    pool = request.app.state.db_pool
    if pool is None:
        return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected"})

    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected"})

    return JSONResponse(status_code=200, content={"status": "ok", "database": "connected"})
