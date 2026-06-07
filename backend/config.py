"""
统一的环境变量配置模块

⚠️ 重要：所有敏感信息必须通过环境变量管理，不要硬编码在代码中！

使用方法：
1. 创建 .env 文件（不要提交到版本控制）
2. 在 .env 文件中设置所需的环境变量
3. 在代码中从本模块导入配置值
"""
import os
from pathlib import Path

# 尝试加载 .env 文件（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    # 从项目根目录查找 .env 文件
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        # override=True：避免 Windows 用户/系统环境里的旧 RESEND_API_KEY 盖掉 .env
        load_dotenv(env_path, override=True)
        print(f"[OK] 已加载环境变量文件: {env_path}")
    else:
        print(f"[WARN] 未找到 .env 文件: {env_path}")
except ImportError:
    print("[WARN] python-dotenv 未安装，将直接从系统环境变量读取")
    pass

# ==================== 必需的环境变量 ====================

# JWT 密钥（用于生成和验证 JWT token）
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    import warnings
    warnings.warn("⚠️ JWT_SECRET 环境变量未设置！生产环境必须设置此变量。")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    import warnings
    warnings.warn("⚠️ OPENAI_API_KEY 环境变量未设置！")

# 数据库环境（development/testing/production）
ENV = os.getenv("ENV", "development")
if ENV not in ["development", "testing", "production"]:
    raise ValueError(f"ENV 必须是 development/testing/production 之一，当前值: {ENV}")

# 数据库 URL（可选，如果设置了则覆盖配置文件中的值）
DATABASE_URL = os.getenv("DATABASE_URL")  # 如果未设置，将使用配置文件中的默认值

# Resend magic-link（可选）
def _normalize_resend_api_key(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lstrip("\ufeff")
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s or None


def _normalize_resend_from_email(raw: str | None) -> str:
    """Strip quotes/BOM; default auth@linktext.app."""
    default = "auth@linktext.app"
    if not raw or not str(raw).strip():
        return default
    s = str(raw).strip().lstrip("\ufeff")
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s or default


RESEND_API_KEY = _normalize_resend_api_key(os.getenv("RESEND_API_KEY"))
# 邮件内登录链接跳转的前端 origin（含协议）
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
RESEND_FROM_EMAIL = _normalize_resend_from_email(os.getenv("RESEND_FROM_EMAIL", "auth@linktext.app"))
# Render 若仍配 onboarding@resend.dev，Resend 只允许发到 Resend 账号邮箱
_db_url = (DATABASE_URL or "").lower()
_on_render_pg = _db_url.startswith("postgresql://") or _db_url.startswith("postgres://")
if (_on_render_pg or ENV == "production") and (
    "@resend.dev" in RESEND_FROM_EMAIL.lower()
    or "onboarding@" in RESEND_FROM_EMAIL.lower()
):
    _prev_from = RESEND_FROM_EMAIL
    RESEND_FROM_EMAIL = "auth@linktext.app"
    print(
        f"[WARN] RESEND_FROM_EMAIL={_prev_from!r} 为 Resend 测试发件人，"
        f"已自动改用 {RESEND_FROM_EMAIL!r}。"
        f"请在 Render Environment 中删除或更新 RESEND_FROM_EMAIL。"
    )
MAGIC_LINK_TTL_MINUTES = int(os.getenv("MAGIC_LINK_TTL_MINUTES", "30"))
MAGIC_LINK_RESEND_COOLDOWN_SECONDS = int(os.getenv("MAGIC_LINK_RESEND_COOLDOWN_SECONDS", "60"))
AUTH_SESSION_TTL_DAYS = int(os.getenv("AUTH_SESSION_TTL_DAYS", "30"))

# 新用户注册/首次邮箱登录赠送积分（1 积分 = 10_000 token，与邀请码展示一致）
POINTS_PER_TOKEN_UNIT = 10_000
NEW_USER_SIGNUP_POINTS = int(os.getenv("NEW_USER_SIGNUP_POINTS", "80"))

def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


# 生产前端 origin（CORS 白名单兜底；可通过 CORS_ALLOWED_ORIGINS 覆盖/扩展）
PRODUCTION_CORS_ORIGINS = [
    "https://linktext.app",
    "https://www.linktext.app",
    "https://linktext-language.vercel.app",
    "https://www.linktext-language.vercel.app",
]

LOCAL_DEV_CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
]


def _parse_cors_allowed_origins(raw: str | None) -> list[str]:
    """
    浏览器带 Cookie（credentials）时，Access-Control-Allow-Origin 不能为 *。
    未设置 CORS_ALLOWED_ORIGINS 时使用生产 + 本地常见端口。
    生产环境请设置：CORS_ALLOWED_ORIGINS=https://www.linktext.app,https://linktext.app
    多个用英文逗号分隔。
    """
    if raw and raw.strip():
        return [_normalize_origin(o) for o in raw.split(",") if o.strip()]
    return [*PRODUCTION_CORS_ORIGINS, *LOCAL_DEV_CORS_ORIGINS]


def _related_origins(origin: str) -> list[str]:
    """linktext.app ↔ www.linktext.app 成对加入，避免只配其一导致 CORS 失败。"""
    o = _normalize_origin(origin)
    if not o.startswith("http"):
        return []
    extra: list[str] = []
    if o == "https://linktext.app":
        extra.append("https://www.linktext.app")
    elif o == "https://www.linktext.app":
        extra.append("https://linktext.app")
    return extra


def _build_cors_allowed_origins() -> list[str]:
    """合并 CORS_ALLOWED_ORIGINS、FRONTEND_ORIGIN 及关联域，去重（勿带尾部 /）。"""
    origins = _parse_cors_allowed_origins(os.getenv("CORS_ALLOWED_ORIGINS"))
    fo = _normalize_origin(FRONTEND_ORIGIN)
    if fo.startswith("http"):
        origins.append(fo)
        origins.extend(_related_origins(fo))
    # 去重且保持顺序
    seen: set[str] = set()
    out: list[str] = []
    for o in origins:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


CORS_ALLOWED_ORIGINS = _build_cors_allowed_origins()

# ==================== Paddle Billing（可选） ====================

PADDLE_API_KEY = os.getenv("PADDLE_API_KEY")


def _normalize_paddle_secret(raw: str | None) -> str | None:
    """Strip quotes/BOM/whitespace from Paddle webhook secret."""
    if not raw:
        return None
    s = raw.strip().lstrip("\ufeff")
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s or None


PADDLE_WEBHOOK_SECRET = _normalize_paddle_secret(os.getenv("PADDLE_WEBHOOK_SECRET"))
PADDLE_ENV = os.getenv("PADDLE_ENV", "sandbox").strip().lower()
if PADDLE_ENV not in ("sandbox", "production"):
    PADDLE_ENV = "sandbox"

PADDLE_PRICE_PRO = os.getenv("PADDLE_PRICE_PRO")

PRO_MONTHLY_CREDITS = int(os.getenv("PRO_MONTHLY_CREDITS", "1000"))


def paddle_billing_enabled() -> bool:
    """Webhook + Pro 订阅 Price ID 已配置时视为已启用真实支付。"""
    return bool(PADDLE_WEBHOOK_SECRET and PADDLE_PRICE_PRO)

# ==================== 可选的环境变量 ====================

# 其他配置可以在这里添加
# DEBUG = os.getenv("DEBUG", "false").lower() == "true"

