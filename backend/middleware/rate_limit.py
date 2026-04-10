"""
Rate Limit 中间件
用于限制 API 调用频率，防止滥用（特别是 AI 接口）
"""
import os
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import time

# 内存存储：(用户ID, 配置键) -> (请求次数, 时间窗口开始时间)
# 注意：这是简单的内存实现，重启后重置。生产环境建议使用 Redis
# 使用 (user_id, config_key) 作为键，确保不同路径配置有独立的计数器
_rate_limit_storage: Dict[Tuple[int, str], Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

# 请求历史记录：用户ID -> [(时间戳, 路径, 方法), ...]
# 用于调试：查看用户发送了哪些请求
_request_history: Dict[int, list] = defaultdict(list)
_MAX_HISTORY_SIZE = 50  # 每个用户最多记录50条请求历史

# Rate limit 配置
RATE_LIMIT_CONFIG = {
    # AI 接口：每个用户每分钟最多 10 次
    "/api/chat": {
        "max_requests": 10,
        "window_seconds": 60,  # 1 分钟
    },
    # 默认配置：每个用户每分钟最多 300 次（普通接口，不需要太严格）
    "default": {
        "max_requests": 300,
        "window_seconds": 60,
    }
}


def get_rate_limit_config(path: str) -> Tuple[Dict, str]:
    """
    获取指定路径的 rate limit 配置
    
    Returns:
        (配置字典, 配置键) - 配置键用于区分不同的限制类型
    """
    # 精确匹配
    if path in RATE_LIMIT_CONFIG:
        return RATE_LIMIT_CONFIG[path], path
    # 🔧 pending-knowledge 是查询接口，不应该使用 AI 接口的严格限制
    # 使用 startsWith 而不是精确匹配，避免 /api/chat/pending-knowledge 被误判为 /api/chat
    if path.startswith("/api/chat/pending-knowledge"):
        return RATE_LIMIT_CONFIG["default"], "default"
    # 默认配置
    return RATE_LIMIT_CONFIG["default"], "default"


def check_rate_limit(user_id: int, path: str) -> Tuple[bool, int, int]:
    """
    检查用户是否超过 rate limit
    
    Args:
        user_id: 用户ID
        path: API 路径
        
    Returns:
        (是否允许, 剩余请求次数, 重置时间秒数)
    """
    config, config_key = get_rate_limit_config(path)
    max_requests = config["max_requests"]
    window_seconds = config["window_seconds"]
    
    # 使用 (user_id, config_key) 作为存储键，确保不同路径配置有独立的计数器
    storage_key = (user_id, config_key)
    
    current_time = time.time()
    request_count, window_start = _rate_limit_storage[storage_key]
    
    # 如果时间窗口已过期，重置计数
    if current_time - window_start >= window_seconds:
        request_count = 0
        window_start = current_time
        _rate_limit_storage[storage_key] = (request_count, window_start)
    
    # 检查是否超过限制
    if request_count >= max_requests:
        reset_in = int(window_seconds - (current_time - window_start))
        return False, 0, reset_in
    
    # 增加计数
    request_count += 1
    _rate_limit_storage[storage_key] = (request_count, window_start)
    
    remaining = max_requests - request_count
    reset_in = int(window_seconds - (current_time - window_start))
    
    return True, remaining, reset_in


def get_user_request_history(user_id: int) -> list:
    """获取用户的请求历史（用于调试）"""
    return _request_history.get(user_id, [])


def clear_user_request_history(user_id: int = None):
    """清除请求历史（用于调试）"""
    if user_id is None:
        _request_history.clear()
    else:
        _request_history.pop(user_id, None)


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limit 中间件
    
    只对需要认证的接口进行 rate limit（通过 Authorization header 识别用户）
    对于不需要认证的接口（如健康检查），跳过 rate limit
    """
    # 🔧 修复：添加异常处理，避免请求中断时导致 500 错误
    try:
        # Dev-only: allow sandbox stress tests to bypass rate limits.
        # This keeps normal UI behavior intact while enabling high-RPS bursts.
        env = os.getenv("ENV", "development").lower()
        if (
            env != "production"
            and request.url.path == "/api/chat"
            and request.headers.get("x-sandbox-test") == "1"
        ):
            return await call_next(request)

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
        
        # 检查 rate limit（先检查，再记录）
        allowed, remaining, reset_in = check_rate_limit(user_id, request.url.path)
        config, config_key = get_rate_limit_config(request.url.path)
        max_requests = config["max_requests"]
        
        # 记录请求历史（用于调试）
        history = _request_history[user_id]
        history.append((
            time.time(),
            request.url.path,
            request.method,
            f"{remaining}/{max_requests}"
        ))
        # 只保留最近的请求历史
        if len(history) > _MAX_HISTORY_SIZE:
            history.pop(0)
        
        if not allowed:
            # 记录被限流的请求详情
            storage_key = (user_id, config_key)
            current_count = _rate_limit_storage[storage_key][0]
            print(f"🚫 [RateLimit] 用户 {user_id} 触发限制: {request.method} {request.url.path}")
            print(f"   配置类型: {config_key}, 当前窗口内请求数: {current_count}/{max_requests}")
            print(f"   最近 {min(len(history), 10)} 条请求:")
            for ts, path, method, _ in history[-10:]:
                dt = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                print(f"     {dt} {method} {path}")
            headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + reset_in),
                "Retry-After": str(reset_in),
            }
            # IMPORTANT: return a proper 429 response instead of raising inside middleware.
            # Raising here can be reported as 500 depending on middleware ordering/handlers.
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": {
                        "error": "rate_limit_exceeded",
                        "message": "提问过快，请过一分钟后再试",
                        "retry_after": reset_in,
                    }
                },
                headers=headers,
            )
        
        # 添加 rate limit 信息到响应头
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_in)
        
        # 调试日志：记录请求（仅在接近限制时）
        if remaining < 5:
            print(f"⚠️ [RateLimit] 用户 {user_id} 剩余 {remaining} 次请求: {request.method} {request.url.path}")
        
        return response
    except HTTPException:
        # 🔧 重新抛出 HTTPException（包括 429），让 FastAPI 正确处理
        raise
    except Exception as e:
        # 🔧 捕获其他异常（如 EndOfStream），记录但不影响请求处理
        print(f"⚠️ [RateLimit] 中间件处理异常（跳过 rate limit）: {e}")
        # 如果发生异常，跳过 rate limit，让请求继续处理
        return await call_next(request)

