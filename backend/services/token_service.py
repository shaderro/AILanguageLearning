"""
Token 使用记录与扣减服务

⚠️ 重要：必须在 DeepSeek API 调用成功后（即 response 返回后）才调用此服务
不要在 API 调用前扣减 token，因为：
1. API 调用可能失败（网络错误、超时等）
2. 实际使用的 token 数量可能与预估不同
3. 只有 API 成功返回后，response.usage 才是真实的使用量
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from database_system.business_logic.models import User, TokenLog, TokenLedger


def record_token_usage(
    session: Session,
    user_id: int,
    total_tokens: int,
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str = "deepseek-chat",
    assistant_name: Optional[str] = None
) -> dict:
    """
    记录 token 使用并扣减用户余额
    
    执行顺序（必须在同一事务中）：
    1. 从 response.usage 中读取真实 token 使用量
    2. 使用 usage.total_tokens 作为唯一扣减依据
    3. 从 user.token_balance 中扣减
    4. 写入一条 TokenLog
    5. 写入一条 TokenLedger（用于账本记录）
    6. 保存 user 与 log（放在同一个事务中）
    
    Args:
        session: 数据库会话（必须在事务中）
        user_id: 用户 ID
        total_tokens: 本次使用的总 token 数（从 response.usage.total_tokens 获取）
        prompt_tokens: Prompt tokens（从 response.usage.prompt_tokens 获取）
        completion_tokens: Completion tokens（从 response.usage.completion_tokens 获取）
        model_name: 使用的模型名称（默认 "deepseek-chat"）
        assistant_name: 调用的 SubAssistant 名称（如 "AnswerQuestionAssistant"），用于详细统计
    
    Returns:
        dict: 包含扣减后的余额等信息
    """
    # 1. 查询用户（使用行级锁，避免并发问题）
    user = session.query(User).filter(User.user_id == user_id).with_for_update().first()
    if not user:
        raise ValueError(f"用户不存在: user_id={user_id}")
    
    # 2. 检查余额是否充足（可选，根据业务需求决定是否在调用前检查）
    if user.token_balance is None:
        user.token_balance = 0
    
    # 3. 扣减 token（使用 total_tokens 作为唯一扣减依据）
    # ⚠️ 注意：这里不做余额检查，因为 API 已经成功调用
    # 如果余额不足，应该在调用 API 前检查，或者允许负余额（根据业务需求）
    user.token_balance = (user.token_balance or 0) - total_tokens
    user.token_updated_at = datetime.utcnow()
    
    # 4. 创建 TokenLog 记录（详细的使用日志）
    token_log = TokenLog(
        user_id=user_id,
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model_name=model_name,
        assistant_name=assistant_name,
        created_at=datetime.utcnow()
    )
    session.add(token_log)
    # 刷新以获取 token_log.id（需要在创建 TokenLedger 之前）
    session.flush()
    
    # 5. 创建 TokenLedger 记录（账本记录，用于审计）
    token_ledger = TokenLedger(
        user_id=user_id,
        delta=-total_tokens,  # 负数表示消耗
        reason="ai_usage",  # 变动原因：AI 使用
        ref_type="api_call",  # 参考类型：API 调用
        ref_id=f"token_log_{token_log.id}",  # 关联到 TokenLog
        created_at=datetime.utcnow()
    )
    session.add(token_ledger)
    
    # 6. 提交事务（由调用者决定是否立即提交，或在外层事务中统一提交）
    # session.commit()  # 这里不提交，由调用者控制事务
    
    # 7. 返回结果
    return {
        "user_id": user_id,
        "total_tokens_used": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "token_balance_after": user.token_balance,
        "model_name": model_name
    }
