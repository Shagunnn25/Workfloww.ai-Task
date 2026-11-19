from fastapi import APIRouter, Request

from app.models.auth import LoginRequest, LoginResponse
from app.services import auth_service

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    result = await auth_service.login(request.app.state.db_pool, payload.email, payload.password)
    return LoginResponse(**result)
