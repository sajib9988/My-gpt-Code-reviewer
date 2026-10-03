import logging
import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.auth import PasswordResetToken, Session, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.security import create_token, expires_in, hash_password, hash_token, verify_password
from dependencies import get_current_user, require_csrf

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = logging.getLogger(__name__)


def set_session_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    response.set_cookie(
        "csrf_token",
        csrf_token,
        max_age=settings.session_ttl_seconds,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def create_session(database: DatabaseSession, user_id: str, response: Response) -> None:
    session_token = create_token()
    csrf_token = create_token()
    database.add(
        Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=hash_token(session_token),
            csrf_token_hash=hash_token(csrf_token),
            expires_at=expires_in(settings.session_ttl_seconds),
        )
    )
    database.commit()
    set_session_cookies(response, session_token, csrf_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit)])
def register(payload: RegisterRequest, response: Response, database: DatabaseSession = Depends(get_db)) -> User:
    email = payload.email.lower()
    if database.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    create_session(database, user.id, response)
    return user


@router.post("/login", response_model=UserResponse, dependencies=[Depends(rate_limit)])
def login(payload: LoginRequest, response: Response, database: DatabaseSession = Depends(get_db)) -> User:
    user = database.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    create_session(database, user.id, response)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> None:
    if session_token:
        session = database.scalar(select(Session).where(Session.token_hash == hash_token(session_token)))
        if session:
            session.revoked = True
            database.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie("csrf_token", path="/")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/forgot-password", dependencies=[Depends(rate_limit)])
def forgot_password(payload: ForgotPasswordRequest, database: DatabaseSession = Depends(get_db)) -> dict[str, str]:
    user = database.scalar(select(User).where(User.email == payload.email.lower()))
    if user:
        token = create_token()
        database.add(
            PasswordResetToken(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=hash_token(token),
                expires_at=expires_in(900),
            )
        )
        database.commit()
        if settings.environment == "development":
            logger.info("Password reset token for %s: %s", user.email, token)
    return {"message": "If the account exists, password reset instructions have been issued"}


@router.post("/reset-password", dependencies=[Depends(rate_limit)])
def reset_password(payload: ResetPasswordRequest, database: DatabaseSession = Depends(get_db)) -> dict[str, str]:
    reset = database.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(payload.token),
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > expires_in(0),
        )
    )
    if not reset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = database.get(User, reset.user_id)
    user.password_hash = hash_password(payload.password)
    reset.used = True
    database.query(Session).filter(Session.user_id == user.id).update({Session.revoked: True})
    database.commit()
    return {"message": "Password has been reset"}
