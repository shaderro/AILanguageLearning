"""
Rate Limit 中间件
用于限制 API 调用频率，防止滥用（特别是 AI 接口）
"""
from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import time

# 内存存储：用户ID -> (请求次数, 时间窗口开始时间)
# 注意：这是简单的内存实现，重启后重置。生产环境建议使用 Redis
_rate_limit_storage: Dict[int, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

# Rate limit 配置
RATE_LIMIT_CONFIG = {
    # AI 接口：每个用户每分钟最多 20 次
    "/api/chat": {
        "max_requests": 20,
        "window_seconds": 60,  # 1 分钟
    },
    # 默认配置：每个用户每分钟最多 100 次
    "default": {
        "max_requests": 100,
        "window_seconds": 60,
    }
}


def get_rate_limit_config(path: str) -> Dict:
    """获取指定路径的 rate limit 配置"""
    # 精确匹配
    if path in RATE_LIMIT_CONFIG:
        return RATE_LIMIT_CONFIG[path]
    # 默认配置
    return RATE_LIMIT_CONFIG["default"]


def check_rate_limit(user_id: int, path: str) -> Tuple[bool, int, int]:
    """
    检查用户是否超过 rate limit
    
    Args:
        user_id: 用户ID
        path: API 路径
        
    Returns:
        (是否允许, 剩余请求次数, 重置时间秒数)
    """
    config = get_rate_limit_config(path)
    max_requests = config["max_requests"]
    window_seconds = config["window_seconds"]
    
    current_time = time.time()
    request_count, window_start = _rate_limit_storage[user_id]
    
    # 如果时间窗口已过期，重置计数
    if current_time - window_start >= window_seconds:
        request_count = 0
        window_start = current_time
        _rate_limit_storage[user_id] = (request_count, window_start)
    
    # 检查是否超过限制
    if request_count >= max_requests:
        reset_in = int(window_seconds - (current_time - window_start))
        return False, 0, reset_in
    
    # 增加计数
    request_count += 1
    _rate_limit_storage[user_id] = (request_count, window_start)
    
    remaining = max_requests - request_count
    reset_in = int(window_seconds - (current_time - window_start))
    
    return True, remaining, reset_in


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limit 中间件
    
    只对需要认证的接口进行 rate limit（通过 Authorization header 识别用户）
    对于不需要认证的接口（如健康检查），跳过 rate limit
    """
    # 跳过健康检查和文档接口
    if request.url.path in ["/", "/api/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    # 尝试从 Authorization header 获取用户ID
    user_id = None
    authorization = request.headers.get("authorization")
    
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.replace("Bearer ", "")
            from backend.utils.auth import decode_access_token
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                user_id = int(payload["sub"])
        except Exception:
            # Token 解析失败，跳过 rate limit（让认证中间件处理）
            pass
    
    # 如果没有用户ID，跳过 rate limit（可能是公开接口）
    if user_id is None:
        return await call_next(request)
    
    # 检查 rate limit
    allowed, remaining, reset_in = check_rate_limit(user_id, request.url.path)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"请求过于频繁，请 {reset_in} 秒后再试",
                "retry_after": reset_in
            },
            headers={
                "X-RateLimit-Limit": str(get_rate_limit_config(request.url.path)["max_requests"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + reset_in),
                "Retry-After": str(reset_in)
            }
        )
    
    # 添加 rate limit 信息到响应头
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(get_rate_limit_config(request.url.path)["max_requests"])
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_in)
    
    return response

