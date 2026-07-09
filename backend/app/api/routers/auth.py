"""Authentication API routes."""

from fastapi import APIRouter, Depends, Request, status

from app.api.auth_deps import get_current_session_id, get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserPublic,
    UserUpdateRequest,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("user-agent"), request.client.host if request.client else None


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
) -> AuthResponse:
    user_agent, ip_address = _client_meta(request)
    return await AuthService(uow).signup(
        payload,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
) -> AuthResponse:
    user_agent, ip_address = _client_meta(request)
    return await AuthService(uow).login(
        payload,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TokenResponse:
    return await AuthService(uow).refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    session_id: str | None = Depends(get_current_session_id),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    return await AuthService(uow).logout(
        current_user,
        refresh_token=payload.refresh_token,
        session_id=session_id,
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    return await AuthService(uow).forgot_password(payload)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    return await AuthService(uow).reset_password(payload)


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserPublic:
    return await AuthService(uow).get_profile(current_user)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserPublic:
    return await AuthService(uow).update_profile(current_user, payload)
