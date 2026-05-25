"""Send magic-link email via Resend (config-driven)."""
from __future__ import annotations

from urllib.parse import quote

import resend
from resend.exceptions import ResendError

from backend.config import FRONTEND_ORIGIN, RESEND_API_KEY, RESEND_FROM_EMAIL


def send_magic_login_email(*, to_email: str, raw_magic_token: str) -> None:
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured")

    resend.api_key = RESEND_API_KEY

    safe_tok = quote(raw_magic_token, safe="")
    login_url = f"{FRONTEND_ORIGIN.rstrip('/')}/auth/callback?token={safe_tok}"

    try:
        resend.Emails.send(
            {
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Your login link",
                "html": f"""
            <div>
                <h2>Login</h2>
                <p>Click below to continue:</p>
                <a href="{login_url}">Login</a>
                <p>This link expires soon and can only be used once.</p>
            </div>
            """,
            }
        )
    except ResendError as e:
        err = str(e).lower()
        if "invalid" in err and "key" in err:
            raise RuntimeError(
                "Resend API key 无效：请检查项目根目录 .env 中的 RESEND_API_KEY，"
                "或在 Resend 控制台重新生成；若 Windows 环境变量里也有 RESEND_API_KEY，请删除错误的那个。"
            ) from e
        raise
