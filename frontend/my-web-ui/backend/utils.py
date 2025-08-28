from typing import Any, Optional, List
from models import ApiResponse


def create_success_response(data: Any = None, message: str = None) -> ApiResponse:
    """创建成功响应"""
    return ApiResponse(
        status="success",
        data=data,
        error=None,
        message=message
    )


def create_error_response(error: str, data: Any = None) -> ApiResponse:
    """创建错误响应"""
    return ApiResponse(
        status="error",
        data=data,
        error=error,
        message=None
    )
