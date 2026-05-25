"""One-time signup bonus for newly created users (not invite codes)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.config import NEW_USER_SIGNUP_POINTS, POINTS_PER_TOKEN_UNIT
from database_system.business_logic.models import TokenLedger, User


def signup_token_amount() -> int:
    """Token delta for new-user grant: points × 10_000 (80 积分 → 800_000 token)."""
    return NEW_USER_SIGNUP_POINTS * POINTS_PER_TOKEN_UNIT


def grant_new_user_signup_tokens(session: Session, user: User) -> int:
    """
    Credit signup bonus to a brand-new user and write token_ledger (reason=signup_grant).
    Returns granted token amount (0 if disabled).
    """
    grant = signup_token_amount()
    if grant <= 0:
        return 0

    now = datetime.now()
    if user.token_balance is None:
        user.token_balance = 0

    session.add(
        TokenLedger(
            user_id=user.user_id,
            delta=grant,
            reason="signup_grant",
            ref_type="signup",
            ref_id=str(user.user_id),
            created_at=now,
        )
    )
    user.token_balance = (user.token_balance or 0) + grant
    user.token_updated_at = now
    session.add(user)
    session.flush()
    return grant
