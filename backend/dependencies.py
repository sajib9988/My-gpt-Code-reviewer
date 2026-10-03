from datetime import UTC, datetime

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.auth import Session, User
from app.security import hash_token

settings = get_settings()


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    session = database.scalar(
        select(Session).where(
            Session.token_hash == hash_token(session_token),
            Session.revoked.is_(False),
            Session.expires_at > datetime.now(UTC),
        )
    )
    user = database.get(User, session.user_id) if session else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def require_csrf(
    csrf_token: str | None = Cookie(default=None),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    database: DatabaseSession = Depends(get_db),
) -> None:
    session = database.scalar(
        select(Session).where(
            Session.token_hash == hash_token(session_token or ""),
            Session.revoked.is_(False),
            Session.expires_at > datetime.now(UTC),
        )
    )
    if not session or not csrf_token or not csrf_header or csrf_token != csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    if session.csrf_token_hash != hash_token(csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
