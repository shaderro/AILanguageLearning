"""Opaque session token hashing + AuthSession lookup (no InviteCode / credit)."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database_system.business_logic.models import AuthSession, User


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def resolve_auth_session_user(session: Session, raw_token: str) -> Optional[User]:
    if not raw_token:
        return None
    h = sha256_hex(raw_token.strip())
    now = datetime.now()
    row = (
        session.query(AuthSession)
        .filter(
            AuthSession.session_token_hash == h,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .first()
    )
    if row is None:
        return None
    return session.query(User).filter(User.user_id == row.user_id).first()


def revoke_auth_session_by_raw(session: Session, raw_token: str) -> bool:
    """Mark session revoked; returns True if a row was updated."""
    if not raw_token:
        return False
    h = sha256_hex(raw_token.strip())
    row = (
        session.query(AuthSession)
        .filter(
            AuthSession.session_token_hash == h,
            AuthSession.revoked_at.is_(None),
        )
        .first()
    )
    if row is None:
        return False
    row.revoked_at = datetime.now()
    session.add(row)
    return True
