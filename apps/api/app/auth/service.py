from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.orm import UserRecord, UserSessionRecord


password_hasher = PasswordHash.recommended()
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthenticationError(ValueError):
    """Raised when auth input or credentials are invalid."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> str:
    normalized = normalize_email(email)
    if not normalized or not EMAIL_PATTERN.match(normalized):
        raise AuthenticationError("Enter a valid email address.")
    return normalized


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise AuthenticationError("Password must be at least 8 characters.")
    return password


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(session: Session, *, email: str, password: str) -> UserRecord:
    normalized_email = validate_email(email)
    validate_password(password)

    existing = session.scalar(select(UserRecord).where(UserRecord.email == normalized_email))
    if existing is not None:
        raise AuthenticationError("An account with that email already exists.")

    user = UserRecord(email=normalized_email, password_hash=password_hasher.hash(password))
    session.add(user)
    session.flush()
    return user


def verify_login(session: Session, *, email: str, password: str) -> UserRecord:
    normalized_email = validate_email(email)
    user = session.scalar(select(UserRecord).where(UserRecord.email == normalized_email))
    if user is None or not password_hasher.verify(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    return user


def create_session_token(session: Session, *, user: UserRecord) -> str:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    record = UserSessionRecord(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=now + timedelta(days=settings.session_ttl_days),
        last_seen_at=now,
    )
    session.add(record)
    session.flush()
    return token


def get_authenticated_user(session: Session, request: Request, *, update_last_seen: bool = True) -> UserRecord | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return None

    now = datetime.now(timezone.utc)
    session_record = session.scalar(
        select(UserSessionRecord)
        .where(UserSessionRecord.token_hash == hash_token(token))
        .where(UserSessionRecord.revoked_at.is_(None))
        .where(UserSessionRecord.expires_at > now)
    )
    if session_record is None:
        return None

    if update_last_seen:
        session_record.last_seen_at = now

    return session_record.user


def require_authenticated_user(session: Session, request: Request) -> UserRecord:
    user = get_authenticated_user(session, request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def revoke_session_token(session: Session, request: Request) -> None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return

    session_record = session.scalar(
        select(UserSessionRecord)
        .where(UserSessionRecord.token_hash == hash_token(token))
        .where(UserSessionRecord.revoked_at.is_(None))
    )
    if session_record is None:
        return

    session_record.revoked_at = datetime.now(timezone.utc)


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )
