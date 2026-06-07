"""
Paddle Billing webhook 验签与入账逻辑。

前端 Checkout 在 customData 中传入 user_id；支付成功后 Paddle 回调本服务，
在此安全地更新 users.plan 与 token_balance。
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.config import (
    PADDLE_PRICE_PRO,
    PADDLE_WEBHOOK_SECRET,
    POINTS_PER_TOKEN_UNIT,
    PRO_MONTHLY_CREDITS,
    paddle_billing_enabled,
)
from database_system.business_logic.models import PaddleWebhookEvent, User


def verify_paddle_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    """验证 Paddle-Signature（HMAC-SHA256，payload = ts:raw_body）。"""
    if not signature_header or not secret:
        return False

    timestamp: Optional[str] = None
    signatures: list[str] = []
    for part in signature_header.split(";"):
        part = part.strip()
        if part.startswith("ts="):
            timestamp = part[3:]
        elif part.startswith("h1="):
            signatures.append(part[3:])

    if not timestamp or not signatures:
        return False

    # Paddle: HMAC-SHA256 of (ts + ":" + raw_body bytes)，勿 parse/format JSON
    signed_payload = timestamp.encode("utf-8") + b":" + raw_body
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in signatures)


def _parse_user_id(custom_data: Any) -> Optional[int]:
    if not custom_data or not isinstance(custom_data, dict):
        return None
    raw = custom_data.get("user_id") or custom_data.get("userId")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _grant_credits(user: User, credits: int) -> int:
    grant_tokens = credits * POINTS_PER_TOKEN_UNIT
    user.token_balance = (user.token_balance or 0) + grant_tokens
    user.token_updated_at = datetime.now()
    return credits


def _record_event(
    session: Session,
    *,
    event_id: str,
    event_type: str,
    user_id: Optional[int],
    transaction_id: Optional[str],
    price_id: Optional[str],
    credits_granted: int,
) -> PaddleWebhookEvent:
    row = PaddleWebhookEvent(
        event_id=event_id,
        event_type=event_type,
        user_id=user_id,
        transaction_id=transaction_id,
        price_id=price_id,
        credits_granted=credits_granted,
    )
    session.add(row)
    return row


def _event_already_processed(session: Session, event_id: str) -> bool:
    return (
        session.query(PaddleWebhookEvent)
        .filter(PaddleWebhookEvent.event_id == event_id)
        .first()
        is not None
    )


def _handle_transaction_completed(session: Session, data: dict[str, Any]) -> dict[str, Any]:
    status = (data.get("status") or "").lower()
    if status != "completed":
        return {"skipped": True, "reason": f"transaction status={status}"}

    custom_data = data.get("custom_data") or {}
    user_id = _parse_user_id(custom_data)
    if user_id is None:
        return {"skipped": True, "reason": "missing custom_data.user_id"}

    user = session.query(User).filter(User.user_id == user_id).first()
    if user is None:
        return {"skipped": True, "reason": f"user {user_id} not found"}

    transaction_id = data.get("id")
    customer_id = data.get("customer_id")
    subscription_id = data.get("subscription_id")

    if customer_id:
        user.paddle_customer_id = customer_id
    if subscription_id:
        user.paddle_subscription_id = subscription_id

    items = data.get("items") or []
    total_credits = 0
    primary_price_id: Optional[str] = None

    pro_price_id = (PADDLE_PRICE_PRO or "").strip()
    for item in items:
        price = item.get("price") or {}
        price_id = price.get("id")
        if not price_id:
            continue
        primary_price_id = primary_price_id or price_id
        if pro_price_id and price_id == pro_price_id:
            user.plan = "pro"
            total_credits += _grant_credits(user, PRO_MONTHLY_CREDITS)

    if total_credits == 0 and not subscription_id:
        return {"skipped": True, "reason": "no Pro subscription price in transaction items"}

    session.add(user)
    return {
        "user_id": user_id,
        "transaction_id": transaction_id,
        "price_id": primary_price_id,
        "credits_granted": total_credits,
        "plan": user.plan,
    }


def _handle_subscription_activated(session: Session, data: dict[str, Any]) -> dict[str, Any]:
    custom_data = data.get("custom_data") or {}
    user_id = _parse_user_id(custom_data)
    if user_id is None:
        return {"skipped": True, "reason": "missing custom_data.user_id"}

    user = session.query(User).filter(User.user_id == user_id).first()
    if user is None:
        return {"skipped": True, "reason": f"user {user_id} not found"}

    user.plan = "pro"
    if data.get("customer_id"):
        user.paddle_customer_id = data["customer_id"]
    if data.get("id"):
        user.paddle_subscription_id = data["id"]
    user.token_updated_at = datetime.now()
    session.add(user)
    return {"user_id": user_id, "plan": "pro", "credits_granted": 0}


def _handle_subscription_canceled(session: Session, data: dict[str, Any]) -> dict[str, Any]:
    subscription_id = data.get("id")
    user: Optional[User] = None

    custom_data = data.get("custom_data") or {}
    user_id = _parse_user_id(custom_data)
    if user_id is not None:
        user = session.query(User).filter(User.user_id == user_id).first()
    elif subscription_id:
        user = (
            session.query(User)
            .filter(User.paddle_subscription_id == subscription_id)
            .first()
        )

    if user is None:
        return {"skipped": True, "reason": "user not found for subscription cancel"}

    user.plan = "free"
    user.paddle_subscription_id = None
    user.token_updated_at = datetime.now()
    session.add(user)
    return {"user_id": user.user_id, "plan": "free", "credits_granted": 0}


def process_paddle_webhook(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """处理已验签的 Paddle webhook JSON。"""
    if not paddle_billing_enabled():
        return {"skipped": True, "reason": "paddle billing not configured"}

    event_id = payload.get("event_id") or payload.get("notification_id")
    event_type = payload.get("event_type") or ""
    data = payload.get("data") or {}

    if not event_id:
        return {"error": "missing event_id"}

    if _event_already_processed(session, event_id):
        return {"duplicate": True, "event_id": event_id}

    result: dict[str, Any] = {"event_type": event_type}
    credits_granted = 0
    user_id: Optional[int] = None
    transaction_id: Optional[str] = None
    price_id: Optional[str] = None

    if event_type == "transaction.completed":
        tx_result = _handle_transaction_completed(session, data)
        result.update(tx_result)
        if tx_result.get("skipped"):
            session.rollback()
            return result
        credits_granted = tx_result.get("credits_granted") or 0
        user_id = tx_result.get("user_id")
        transaction_id = tx_result.get("transaction_id")
        price_id = tx_result.get("price_id")
    elif event_type == "subscription.activated":
        sub_result = _handle_subscription_activated(session, data)
        result.update(sub_result)
        if sub_result.get("skipped"):
            session.rollback()
            return result
        user_id = sub_result.get("user_id")
    elif event_type in ("subscription.canceled", "subscription.past_due"):
        sub_result = _handle_subscription_canceled(session, data)
        result.update(sub_result)
        if sub_result.get("skipped"):
            session.rollback()
            return result
        user_id = sub_result.get("user_id")
    else:
        _record_event(
            session,
            event_id=event_id,
            event_type=event_type,
            user_id=None,
            transaction_id=None,
            price_id=None,
            credits_granted=0,
        )
        session.commit()
        return {"acknowledged": True, "event_type": event_type, "handled": False}

    _record_event(
        session,
        event_id=event_id,
        event_type=event_type,
        user_id=user_id,
        transaction_id=transaction_id,
        price_id=price_id,
        credits_granted=credits_granted,
    )
    session.commit()
    result["handled"] = True
    result["event_id"] = event_id
    return result


def verify_and_process_webhook(
    session: Session,
    raw_body: bytes,
    signature_header: str,
) -> tuple[int, dict[str, Any]]:
    """
    验签并处理 webhook。
    返回 (http_status, body_dict)。
    """
    secret = PADDLE_WEBHOOK_SECRET or ""
    if not secret:
        return 503, {"error": "paddle webhook secret not configured"}

    if not verify_paddle_signature(raw_body, signature_header, secret):
        hint = ""
        if secret.startswith("ntfset_") and not secret.startswith("pdl_ntfset_"):
            hint = (
                " (looks like notification destination ID — use endpoint_secret_key "
                "from Paddle Notifications, format pdl_ntfset_XXXXXXXX_YYYYYYYY)"
            )
        print(
            "❌ [Paddle] webhook signature invalid — "
            f"has_header={bool(signature_header.strip())}, "
            f"body_len={len(raw_body)}, "
            f"secret_prefix={(secret[:20] + '...') if len(secret) > 20 else secret}"
            f"{hint}"
        )
        return 401, {"error": "invalid signature"}

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 400, {"error": "invalid json"}

    try:
        result = process_paddle_webhook(session, payload)
        return 200, result
    except Exception as exc:
        session.rollback()
        print(f"❌ [Paddle] webhook processing failed: {exc}")
        return 500, {"error": "processing failed"}
