"""统一响应格式模块。

提供标准 JSON 响应结构 {"code": ..., "msg": "...", "data": {...}}，支持 AES 加密开关。
修复原始版本中的 bug：
- resp_401 正确返回 HTTP 401 状态码（原版错误地返回 400）
- exception_400 / exception_401 不再重名
"""

import json
from typing import Any, Optional

from fastapi import HTTPException, Response, status

from app.core.json_response import MyEncoder
from app.core.config import settings


class MyResponse(Response):
    """自定义 JSON 响应类，使用 MyEncoder 处理 Decimal / datetime 等类型。"""

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=MyEncoder,
        ).encode("utf-8")


def _maybe_encrypt(data: Any) -> Any:
    """当配置启用 AES 加密时，对 data 进行加密。"""
    if getattr(settings, "IS_AESCRYPT", False):
        from app.core.aes import Aescrypt  # 懒加载，避免循环引用
        aes = Aescrypt(settings.AES_KEY)
        json_str = json.dumps(
            data,
            ensure_ascii=True,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=MyEncoder,
        )
        return aes.encrypt(json_str)
    return data


def resp_200(
    code: int = 200,
    msg: str = "",
    data: Any = None,
    headers: Optional[dict] = None,
) -> MyResponse:
    """返回 200 成功响应。"""
    return MyResponse(
        status_code=200,
        content={"code": code, "msg": msg, "data": _maybe_encrypt(data)},
        headers=headers,
    )


def resp_400(
    code: int = 400,
    msg: str = "",
    data: Any = None,
    headers: Optional[dict] = None,
) -> MyResponse:
    """返回 400 客户端错误响应。"""
    return MyResponse(
        status_code=400,
        content={"code": code, "msg": msg, "data": data},
        headers=headers,
    )


def resp_401(
    code: int = 401,
    msg: str = "",
    data: Any = None,
    headers: Optional[dict] = None,
) -> MyResponse:
    """返回 401 未授权响应。"""
    return MyResponse(
        status_code=401,
        content={"code": code, "msg": msg, "data": data},
        headers=headers,
    )


def exception_400(msg: str = "", headers: Optional[dict] = None) -> None:
    """抛出 400 Bad Request 异常。"""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": 400, "msg": msg},
        headers=headers,
    )


def exception_401(msg: str = "", headers: Optional[dict] = None) -> None:
    """抛出 401 Unauthorized 异常。"""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": 401, "msg": msg},
        headers=headers,
    )
