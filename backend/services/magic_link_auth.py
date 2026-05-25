"""Magic-link lifecycle: create token, send email, consume -> User + AuthSession."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from database_system.business_logic.models import AuthSession, MagicLinkToken, User
from backend.utils.auth import hash_password
from backend.utils.session_auth import new_opaque_token, sha256_hex

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _find_user_by_email_ci(session: Session, email_norm: str) -> Optional[User]:
    return (
        session.query(User)
        .filter(func.lower(User.email) == email_norm)
        .first()
    )


def create_and_send_magic_link(session: Session, email: str) -> None:
    """
    Replace any pending tokens for this email, insert new MagicLinkToken, send Resend email.
    Raises on email send failure (caller maps to HTTP).
    """
    from backend.services.magic_link_email import send_magic_login_email

    email_norm = normalize_email(email)
    if not email_norm or "@" not in email_norm:
        raise ValueError("invalid_email")

    session.query(MagicLinkToken).filter(
        MagicLinkToken.email == email_norm,
        MagicLinkToken.used_at.is_(None),
    ).delete(synchronize_session=False)

    raw = new_opaque_token()
    th = sha256_hex(raw)

    from backend.config import MAGIC_LINK_TTL_MINUTES

    expires = datetime.now() + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)
    row = MagicLinkToken(email=email_norm, token_hash=th, expires_at=expires)
    session.add(row)
    session.flush()

    send_magic_login_email(to_email=email_norm, raw_magic_token=raw)


def consume_magic_link(
    session: Session, raw_magic_token: str, session_ttl_days: int
) -> Tuple[User, str]:
    """
    Validate one-time token, mark used, find-or-create User, create AuthSession.
    Returns (user, raw_session_token for Set-Cookie / Authorization).
    """
    if not raw_magic_token or not raw_magic_token.strip():
        raise ValueError("missing_token")

    th = sha256_hex(raw_magic_token.strip())
    now = datetime.now()
    m = (
        session.query(MagicLinkToken)
        .filter(
            MagicLinkToken.token_hash == th,
            MagicLinkToken.used_at.is_(None),
            MagicLinkToken.expires_at > now,
        )
        .first()
    )
    if m is None:
        raise ValueError("invalid_or_expired_token")

    m.used_at = now
    session.add(m)

    email_norm = m.email
    user = _find_user_by_email_ci(session, email_norm)
    if user is None:
        import secrets as sec

        from backend.services.signup_token_grant import grant_new_user_signup_tokens

        user = User(
            password_hash=hash_password(sec.token_urlsafe(32)),
            email=email_norm,
        )
        session.add(user)
        session.flush()
        grant_new_user_signup_tokens(session, user)

    raw_session = new_opaque_token()
    sess = AuthSession(
        session_token_hash=sha256_hex(raw_session),
        user_id=user.user_id,
        expires_at=now + timedelta(days=session_ttl_days),
    )
    session.add(sess)
    session.flush()

    return user, raw_session
