"""
Send a test email via Resend (magic-link style HTML).

From repo root, after RESEND_API_KEY is set in .env (or environment):

  pip install resend
  python backend/scripts/resend_test_email.py --to you@example.com

If .env and Windows both define RESEND_API_KEY, this script loads .env with
override=True so the file wins (avoids stale system keys).

Use --debug-key to print masked length/prefix when troubleshooting.

With auth@linktext.app, linktext.app must be verified in Resend.
Use onboarding@resend.dev locally if the domain is not verified yet.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _normalize_resend_api_key(raw: str | None) -> str | None:
    """Strip .env / copy-paste junk so Resend sees the real key (re_...)."""
    if not raw:
        return None
    s = raw.strip().lstrip("\ufeff")
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s or None


def send_magic_link(email: str, token: str, from_email: str):
    import resend

    login_url = f"http://localhost:3000/auth/callback?token={token}"

    return resend.Emails.send(
        {
            "from": from_email,
            "to": email,
            "subject": "Your login link",
            "html": f"""
            <div>
                <h2>Login to LinkText</h2>
                <p>Click below to continue:</p>
                <a href="{login_url}">Login</a>
                <p>This link will expire soon.</p>
            </div>
        """,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a Resend test (magic link).")
    parser.add_argument(
        "--to",
        default=os.getenv("RESEND_TEST_TO", ""),
        help="Recipient (default: RESEND_TEST_TO env)",
    )
    parser.add_argument(
        "--token",
        default="test-token-resend",
        help="Token embedded in the callback URL",
    )
    parser.add_argument(
        "--debug-key",
        action="store_true",
        help="Print masked key length/prefix to stderr (troubleshooting only).",
    )
    args = parser.parse_args()
    if not args.to:
        print("Missing recipient: use --to you@example.com or set RESEND_TEST_TO.", file=sys.stderr)
        return 2

    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore[assignment]
    # override=True: if Windows has a stale RESEND_API_KEY, default load_dotenv
    # would keep it and ignore .env — a very common cause of "invalid" keys.
    if load_dotenv:
        load_dotenv(REPO_ROOT / ".env", override=True)

    key = _normalize_resend_api_key(os.getenv("RESEND_API_KEY"))
    if not key:
        print(
            "RESEND_API_KEY is not set. Add it to .env at the repo root or export it.",
            file=sys.stderr,
        )
        return 1

    if args.debug_key:
        preview = f"{key[:7]}...{key[-4:]}" if len(key) > 14 else "(too short)"
        print(
            f"[debug] key len={len(key)} preview={preview} re_prefix={key.startswith('re_')}",
            file=sys.stderr,
        )

    import resend
    from resend.exceptions import ResendError

    sys.path.insert(0, str(REPO_ROOT))
    from backend.config import RESEND_FROM_EMAIL

    resend.api_key = key
    try:
        response = send_magic_link(args.to, args.token, RESEND_FROM_EMAIL)
    except ResendError as e:
        err = str(e).lower()
        print(f"Resend error: {e}", file=sys.stderr)
        if "invalid" in err and "key" in err:
            print(
                "This response means Resend received a key but rejected it (not a read failure).\n"
                "Check: full key from Resend API Keys page (starts with re_), no spaces/newlines, "
                "no smart quotes in .env.\n"
                "If you ever set RESEND_API_KEY in Windows User/System environment variables, "
                "a wrong value there used to win over .env; this script now forces .env with override=True — "
                "remove bad system entries or fix .env.\n"
                "Re-run with --debug-key to confirm length/prefix. Regenerate the key in Resend if unsure.",
                file=sys.stderr,
            )
        return 1
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
