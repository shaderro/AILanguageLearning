"""
Paddle Billing API：webhook 接收端点。
"""
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.db_deps import get_db_session
from backend.config import paddle_billing_enabled
from backend.services.paddle_billing import verify_and_process_webhook

router = APIRouter(
    prefix="/api/billing",
    tags=["billing"],
)


class BillingStatusResponse(BaseModel):
    paddle_enabled: bool


@router.get("/status", response_model=BillingStatusResponse)
async def billing_status():
    """前端可用来判断是否应走真实 Paddle Checkout（模拟接口在启用 Paddle 后会被禁用）。"""
    return BillingStatusResponse(paddle_enabled=paddle_billing_enabled())


@router.post("/webhooks/paddle")
async def paddle_webhook(
    request: Request,
    session: Session = Depends(get_db_session),
    paddle_signature: str = Header(default="", alias="Paddle-Signature"),
):
    """
    Paddle Billing webhook。在 Paddle Dashboard → Developer tools → Notifications 配置：
    https://your-api-host/api/billing/webhooks/paddle
    """
    raw_body = await request.body()
    signature = paddle_signature or request.headers.get("paddle-signature", "")
    status_code, body = verify_and_process_webhook(session, raw_body, signature)
    return JSONResponse(status_code=status_code, content=body)
