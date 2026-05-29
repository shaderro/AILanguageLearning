"""Magic-link lifecycle: create token, send email, consume -> User + AuthSession."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

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


def create_and_send_magic_link(session: Session, email: str) -> Dict[str, Any]:
    """
    Replace any pending tokens for this email, insert new MagicLinkToken, send Resend email.
    Within MAGIC_LINK_RESEND_COOLDOWN_SECONDS, skips sending another email (returns retry_after_seconds).
    Raises on email send failure (caller maps to HTTP).
    """
    from backend.services.magic_link_email import send_magic_login_email
    from backend.config import MAGIC_LINK_RESEND_COOLDOWN_SECONDS

    email_norm = normalize_email(email)
    if not email_norm or "@" not in email_norm:
        raise ValueError("invalid_email")

    now = datetime.now()
    latest = (
        session.query(MagicLinkToken)
        .filter(
            MagicLinkToken.email == email_norm,
            MagicLinkToken.used_at.is_(None),
            MagicLinkToken.expires_at > now,
        )
        .order_by(MagicLinkToken.created_at.desc())
        .first()
    )
    if latest is not None:
        elapsed = (now - latest.created_at).total_seconds()
        if elapsed < MAGIC_LINK_RESEND_COOLDOWN_SECONDS:
            retry_after = int(MAGIC_LINK_RESEND_COOLDOWN_SECONDS - elapsed)
            return {"sent": False, "retry_after_seconds": max(1, retry_after)}

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
    return {"sent": True, "retry_after_seconds": MAGIC_LINK_RESEND_COOLDOWN_SECONDS}


def _issue_session_for_user(
    session: Session, user: User, session_ttl_days: int, now: datetime
) -> str:
    raw_session = new_opaque_token()
    sess = AuthSession(
        session_token_hash=sha256_hex(raw_session),
        user_id=user.user_id,
        expires_at=now + timedelta(days=session_ttl_days),
    )
    session.add(sess)
    session.flush()
    return raw_session


def consume_magic_link(
    session: Session, raw_magic_token: str, session_ttl_days: int
) -> Tuple[User, str, bool]:
    """
    Validate one-time token, mark used, find-or-create User, create AuthSession.
    Returns (user, raw_session_token, is_new_user).

    Raises ValueError with a short detail code for HTTP mapping:
    missing_token | link_expired | link_used | link_invalid
    """
    token = (raw_magic_token or "").strip()
    if not token:
        raise ValueError("missing_token")

    th = sha256_hex(token)
    now = datetime.now()
    m_any = (
        session.query(MagicLinkToken)
        .filter(MagicLinkToken.token_hash == th)
        .first()
    )

    # 已使用：5 分钟内允许重复校验（防重复点击 / 页面重复挂载）
    if m_any is not None and m_any.used_at is not None:
        elapsed = (now - m_any.used_at).total_seconds()
        if elapsed <= 300:
            user = _find_user_by_email_ci(session, m_any.email)
            if user is not None:
                raw_session = _issue_session_for_user(session, user, session_ttl_days, now)
                return user, raw_session, False
        raise ValueError("link_used")

    m = (
        session.query(MagicLinkToken)
        .filter(
            MagicLinkToken.token_hash == th,
            MagicLinkToken.used_at.is_(None),
        )
        .first()
    )
    if m is None:
        raise ValueError("link_invalid")
    if m.expires_at <= now:
        raise ValueError("link_expired")

    m.used_at = now
    session.add(m)

    email_norm = m.email
    user = _find_user_by_email_ci(session, email_norm)
    is_new_user = False
    if user is None:
        import secrets as sec

        from backend.services.signup_token_grant import grant_new_user_signup_tokens

        is_new_user = True

        user = User(
            password_hash=hash_password(sec.token_urlsafe(32)),
            email=email_norm,
        )
        session.add(user)
        session.flush()
        grant_new_user_signup_tokens(session, user)

    raw_session = _issue_session_for_user(session, user, session_ttl_days, now)
    return user, raw_session, is_new_user
