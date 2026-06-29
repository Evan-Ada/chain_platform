"""日志配置与请求日志装饰器模块。

提供：
- loguru 全局日志配置（5MB 轮转、5 天保留、UTF-8、enqueue）
- @add_log 装饰器：记录请求耗时、慢请求告警、失败日志、可选微信通知
"""

import asyncio
import time
import os
from functools import wraps
from typing import Callable, Optional

from loguru import logger

# ---------------------------------------------------------------------------
# loguru 配置
# ---------------------------------------------------------------------------
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_log_path = os.path.join(_base_dir, "logs")

os.makedirs(_log_path, exist_ok=True)

_log_file = os.path.join(_log_path, "{time:YYYY-MM-DD}.log")


def _get_log_level() -> str:
    try:
        from app.core.config import settings
        return getattr(settings, "LOG_LEVEL", "DEBUG")
    except Exception:
        return "DEBUG"


logger.add(
    _log_file,
    rotation="5 MB",
    retention="5 days",
    enqueue=True,
    encoding="utf-8",
    level=_get_log_level(),
)


# ---------------------------------------------------------------------------
# @add_log 装饰器
# ---------------------------------------------------------------------------
def add_log(notify: bool = False):
    """请求日志记录装饰器（支持同步与异步函数）。

    功能：
    - 记录请求耗时（毫秒）
    - 慢请求警告：> SLOW_REQUEST_THRESHOLD（默认 0.5s）
    - 慢请求错误：> ERROR_REQUEST_THRESHOLD（默认 1.5s）
    - 非 200 响应记录为 error
    - 可选微信通知（notify=True 且 ENABLE_WECHAT_NOTIFY 开启时）

    Args:
        notify: 是否在异常时发送微信通知。
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _execute_with_log(func, notify, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _execute_sync_with_log(func, notify, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


async def _execute_with_log(func: Callable, notify: bool, *args, **kwargs):
    """异步函数的日志记录逻辑。"""
    func_name = func.__name__
    start_time = time.time()

    try:
        response = await func(*args, **kwargs)
    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[{func_name}] 执行异常 ({elapsed_ms}ms): {e}")
        if notify:
            _try_notify(func_name, elapsed_ms, str(e))
        raise

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    _log_response(func_name, elapsed_ms, response, notify)
    return response


def _execute_sync_with_log(func: Callable, notify: bool, *args, **kwargs):
    """同步函数的日志记录逻辑。"""
    func_name = func.__name__
    start_time = time.time()

    try:
        response = func(*args, **kwargs)
    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[{func_name}] 执行异常 ({elapsed_ms}ms): {e}")
        if notify:
            _try_notify(func_name, elapsed_ms, str(e))
        raise

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    _log_response(func_name, elapsed_ms, response, notify)
    return response


def _log_response(func_name: str, elapsed_ms: float, response, notify: bool):
    """根据响应状态码和耗时记录日志。"""
    from app.core.config import settings

    slow_threshold = getattr(settings, "SLOW_REQUEST_THRESHOLD", 0.5)
    error_threshold = getattr(settings, "ERROR_REQUEST_THRESHOLD", 1.5)

    status_code = getattr(response, "status_code", 200)
    elapsed_sec = elapsed_ms / 1000

    msg = f"[{func_name}] {status_code} | {elapsed_ms}ms"

    if status_code != 200:
        logger.error(msg)
        if notify:
            _try_notify(func_name, elapsed_ms, f"status={status_code}")
    elif elapsed_sec >= error_threshold:
        logger.error(f"慢请求(严重) {msg}")
        if notify:
            _try_notify(func_name, elapsed_ms, "严重慢请求")
    elif elapsed_sec >= slow_threshold:
        logger.warning(f"慢请求 {msg}")
    else:
        logger.info(msg)


def _try_notify(func_name: str, elapsed_ms: float, error_info: str):
    """尝试发送微信通知，失败不影响主流程。"""
    from app.core.config import settings

    if not getattr(settings, "ENABLE_WECHAT_NOTIFY", False):
        return

    try:
        from app.core.notification import send_template_message

        send_template_message(
            title="接口异常告警",
            content=f"{func_name} | {elapsed_ms}ms | {error_info}",
        )
    except Exception as e:
        logger.warning(f"微信通知发送失败: {e}")
