"""
邀请码 / Token 额度 API 路由

- 目前提供：
  - POST /api/invite/redeem  兑换一次性邀请码，发放 1,000,000 token
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.auth_routes import get_current_user
from backend.api.db_deps import get_db_session
from database_system.business_logic.models import User, InviteCode, TokenLedger


router = APIRouter(
    prefix="/api/invite",
    tags=["invite"],
)


class RedeemInviteRequest(BaseModel):
    """兑换邀请码请求体"""

    code: str = Field(..., min_length=1, description="邀请码字符串（不区分大小写）")


class RedeemInviteResponse(BaseModel):
    """兑换邀请码响应体（用于文档说明；实际返回为 dict）"""

    success: bool
    data: dict
    message: Optional[str] = None


@router.post(
    "/redeem",
    summary="兑换一次性邀请码，获取 token 额度",
    response_model=RedeemInviteResponse,
)
async def redeem_invite(
    request: RedeemInviteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """
    兑换一次性邀请码：

    步骤：
    1. 将用户输入的 code 统一转为大写（实现大小写不敏感）
    2. 在 invite_codes 表中查找满足条件的记录：
       - code 匹配
       - status = 'active'
       - redeemed_by_user_id IS NULL
       - (expires_at IS NULL OR expires_at > now)
    3. 找不到则返回 400（邀请码无效 / 已使用 / 已过期）
    4. 找到则在事务中执行：
       - 往 token_ledger 写入一条正向变动记录（invite_grant）
       - 更新当前用户的 token_balance 和 token_updated_at
       - 标记邀请码为 redeemed，并记录 redeemed_by_user_id / redeemed_at
    5. 返回新的 token 余额等信息
    """
    raw_code = request.code.strip()
    if not raw_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码不能为空",
        )

    normalized_code = raw_code.upper()
    now = datetime.utcnow()

    # 查询可用的邀请码，使用行级锁避免并发重复兑换（PostgreSQL 生效，SQLite 忽略）
    invite: Optional[InviteCode] = (
        session.query(InviteCode)
        .with_for_update()  # 在支持的数据库上加锁
        .filter(
            InviteCode.code == normalized_code,
            InviteCode.status == "active",
            InviteCode.redeemed_by_user_id.is_(None),
        )
        .first()
    )

    # 校验有效性（包含过期判断）
    if (
        invite is None
        or (invite.expires_at is not None and invite.expires_at <= now)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码无效、已使用或已过期",
        )

    # 计算发放额度
    grant = invite.token_grant or 0
    if grant <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邀请码配置的 token 数量无效",
        )

    # 确保用户当前余额为整数
    if current_user.token_balance is None:
        current_user.token_balance = 0

    # 🔧 如果用户token balance为负数，先更新为0，再增加邀请码的token
    current_balance = current_user.token_balance or 0
    if current_balance < 0:
        # 先归零的变动记录
        zero_ledger_entry = TokenLedger(
            user_id=current_user.user_id,
            delta=-current_balance,  # 负数变0需要的正数变动
            reason="invite_grant_zero_adjustment",
            ref_type="invite_code",
            ref_id=normalized_code,
            created_at=now,
        )
        session.add(zero_ledger_entry)
        current_balance = 0

    # 写入 token 账本记录（邀请码发放）
    ledger_entry = TokenLedger(
        user_id=current_user.user_id,
        delta=grant,
        reason="invite_grant",
        ref_type="invite_code",
        ref_id=normalized_code,
        created_at=now,
    )
    session.add(ledger_entry)

    # 更新用户余额
    current_user.token_balance = current_balance + grant
    current_user.token_updated_at = now

    # 标记邀请码为已兑换（单用户生效）
    invite.status = "redeemed"
    invite.redeemed_by_user_id = current_user.user_id
    invite.redeemed_at = now

    # 提示信息（返回给前端）
    message = f"邀请码兑换成功，获得 {grant} 个 token，当前余额为 {current_user.token_balance}"

    return {
        "success": True,
        "data": {
            "code": normalized_code,
            "granted_tokens": grant,
            "token_balance": current_user.token_balance,
            "redeemed_at": now.isoformat(),
        },
        "message": message,
    }

