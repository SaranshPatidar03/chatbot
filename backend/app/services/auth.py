"""Authentication use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.deps import UnitOfWork
from app.db.enums import AnalyticsEventType, PlatformRole
from app.db.models.session import PasswordResetToken, UserSession
from app.db.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserPublic,
    UserUpdateRequest,
)
from app.utils.email import send_password_reset_email

logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AuthService:
    """Signup, login, token rotation, password reset, and profile management."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    @staticmethod
    def _user_public(user: User) -> UserPublic:
        return UserPublic.model_validate(user)

    async def _create_session(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str]:
        """Persist a refresh session and return access + refresh JWTs."""
        settings = self.settings
        expires_at = _utc_now() + timedelta(days=settings.refresh_token_expire_days)
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(generate_opaque_token()),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        session = await self.uow.sessions.add(session)

        access_token = create_access_token(user.id, session_id=session.id)
        refresh_token = create_refresh_token(user.id, session_id=session.id)
        session.refresh_token_hash = hash_token(refresh_token)
        await self.uow.session.flush()
        await self.uow.session.refresh(session)
        return access_token, refresh_token

    async def _auth_response(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthResponse:
        access_token, refresh_token = await self._create_session(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=self._user_public(user),
        )

    async def signup(
        self,
        payload: SignupRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthResponse:
        email = payload.email.lower().strip()
        if await self.uow.users.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user = User(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name.strip() if payload.full_name else None,
            role=(
                PlatformRole.PLATFORM_ADMIN.value
                if self.settings.initial_admin_email
                and email == self.settings.initial_admin_email.lower().strip()
                else PlatformRole.USER.value
            ),
            is_active=True,
            is_verified=False,
        )
        user = await self.uow.users.add(user)
        await self.uow.settings.get_or_create(user.id)

        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="auth.signup",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.AUTH.value,
            name="signup",
            status="success",
        )

        logger.info("user_signup", user_id=user.id, email=email)
        return await self._auth_response(user, user_agent=user_agent, ip_address=ip_address)

    async def login(
        self,
        payload: LoginRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthResponse:
        email = payload.email.lower().strip()
        user = await self.uow.users.get_by_email(email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )

        user.last_login_at = _utc_now()
        await self.uow.session.flush()

        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="auth.login",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.AUTH.value,
            name="login",
            status="success",
        )

        logger.info("user_login", user_id=user.id, email=email)
        return await self._auth_response(user, user_agent=user_agent, ip_address=ip_address)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            claims = decode_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            ) from exc

        if claims.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )

        session_id = claims.get("sid")
        user_id = claims.get("sub")
        if not session_id or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed refresh token.",
            )

        session = await self.uow.sessions.get_by_id(session_id)
        if (
            not session
            or session.user_id != user_id
            or session.is_revoked
            or _as_utc(session.expires_at) <= _utc_now()
            or session.refresh_token_hash != hash_token(refresh_token)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session is no longer valid.",
            )

        user = await self.uow.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is unavailable.",
            )

        access_token = create_access_token(user.id, session_id=session.id)
        new_refresh = create_refresh_token(user.id, session_id=session.id)
        session.refresh_token_hash = hash_token(new_refresh)
        await self.uow.session.flush()

        return TokenResponse(access_token=access_token, refresh_token=new_refresh)

    async def logout(
        self,
        user: User,
        *,
        refresh_token: str | None = None,
        session_id: str | None = None,
    ) -> MessageResponse:
        if refresh_token:
            token_hash = hash_token(refresh_token)
            session = await self.uow.sessions.get_by_token_hash(token_hash)
            if session and session.user_id == user.id and not session.is_revoked:
                await self.uow.sessions.revoke(session)
        elif session_id:
            session = await self.uow.sessions.get_by_id(session_id)
            if session and session.user_id == user.id and not session.is_revoked:
                await self.uow.sessions.revoke(session)
        else:
            await self.uow.sessions.revoke_all_for_user(user.id)

        await self.uow.audit_logs.record(actor_id=user.id, action="auth.logout")
        return MessageResponse(message="Logged out successfully.")

    async def forgot_password(self, payload: ForgotPasswordRequest) -> MessageResponse:
        email = payload.email.lower().strip()
        user = await self.uow.users.get_by_email(email)
        message = MessageResponse(
            message="If that email exists, password reset instructions have been sent.",
        )
        if not user or not user.is_active:
            return message

        raw_token = generate_opaque_token()
        expires_at = _utc_now() + timedelta(
            minutes=self.settings.password_reset_token_expire_minutes,
        )
        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        await self.uow.password_resets.add(reset)

        try:
            await send_password_reset_email(to_email=user.email, reset_token=raw_token)
        except Exception as exc:  # noqa: BLE001 — log but do not leak existence
            logger.exception("password_reset_email_failed", user_id=user.id, error=str(exc))

        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="auth.forgot_password",
            details={"email": email},
        )
        return message

    async def reset_password(self, payload: ResetPasswordRequest) -> MessageResponse:
        token_hash = hash_token(payload.token)
        reset = await self.uow.password_resets.get_by_token_hash(token_hash)
        if (
            not reset
            or reset.used_at is not None
            or _as_utc(reset.expires_at) <= _utc_now()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        user = await self.uow.users.get_by_id(reset.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        user.hashed_password = hash_password(payload.password)
        await self.uow.password_resets.mark_used(reset)
        await self.uow.sessions.revoke_all_for_user(user.id)
        await self.uow.session.flush()

        await self.uow.audit_logs.record(actor_id=user.id, action="auth.reset_password")
        logger.info("password_reset", user_id=user.id)
        return MessageResponse(message="Password updated successfully.")

    async def get_profile(self, user: User) -> UserPublic:
        return self._user_public(user)

    async def update_profile(self, user: User, payload: UserUpdateRequest) -> UserPublic:
        if payload.full_name is not None:
            user.full_name = payload.full_name.strip() or None
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url.strip() or None
        await self.uow.session.flush()
        await self.uow.session.refresh(user)
        return self._user_public(user)
