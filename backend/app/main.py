import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, employees, health, tasks
from app.core.config import settings
from app.core.database import create_db_pool

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.db_pool = await create_db_pool()
    except Exception:
        # Let the app come up even if the DB is unreachable at startup;
        # /health will report the failure instead of the whole API 500ing.
        logger.exception("Failed to create database pool at startup")
        app.state.db_pool = None
    yield
    if app.state.db_pool is not None:
        await app.state.db_pool.close()


app = FastAPI(title="Task Management API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_ERROR_CODES = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # One consistent {error, message} shape for every HTTPException we raise,
    # instead of FastAPI's default {"detail": ...}.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": _ERROR_CODES.get(exc.status_code, "error"), "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": "Invalid request data."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internal error details (stack traces, DB errors) to clients.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "Something went wrong."},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(employees.router)
