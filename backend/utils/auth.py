"""
认证工具模块
提供密码加密、JWT token 生成和验证功能
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt

# 从统一配置模块导入
try:
    from backend.config import JWT_SECRET
    SECRET_KEY = JWT_SECRET or "your-secret-key-change-in-production"
except ImportError:
    # 如果导入失败，直接从环境变量读取（向后兼容）
    import os
    SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# JWT 配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


def hash_password(password: str) -> str:
    """
    加密密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 加密后的密码哈希
    """
    # 将密码编码为字节
    password_bytes = password.encode('utf-8')
    # 生成盐并加密
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # 返回字符串形式
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希
        
    Returns:
        bool: 密码是否匹配
    """
    # 将字符串转换为字节
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # 验证密码
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token
    
    Args:
        data: 要编码到 token 中的数据（通常包含 user_id）
        expires_delta: token 过期时间，默认为配置的过期时间
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码并验证 JWT token
    
    Args:
        token: JWT token 字符串
        
    Returns:
        dict: 解码后的数据，如果 token 无效则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_password_reset_token(user_id: int) -> str:
    """
    创建密码重置 token
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: 密码重置 token（1小时有效）
    """
    expire = datetime.utcnow() + timedelta(hours=1)  # 1小时过期
    to_encode = {
        "sub": str(user_id),
        "type": "password_reset",  # 标记为密码重置 token
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_password_reset_token(token: str) -> Optional[int]:
    """
    解码并验证密码重置 token
    
    Args:
        token: 密码重置 token 字符串
        
    Returns:
        int: 用户ID，如果 token 无效则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 验证 token 类型
        if payload.get("type") != "password_reset":
            return None
        user_id_str = payload.get("sub")
        if user_id_str:
            return int(user_id_str)
        return None
    except (JWTError, ValueError, TypeError):
        return None
