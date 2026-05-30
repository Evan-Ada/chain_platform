"""时间工具模块。

提供 UTC 时区感知的当前时间获取与格式化函数。
"""

from datetime import datetime, timezone


def get_now() -> datetime:
    """返回当前 UTC 时间（时区感知）。"""
    return datetime.now(timezone.utc)


def get_now_str() -> str:
    """返回当前 UTC 时间的字符串，格式 'YYYY-MM-DD HH:MM:SS'。"""
    return get_now().strftime("%Y-%m-%d %H:%M:%S")


def get_now_str_compact() -> str:
    """返回当前 UTC 时间的紧凑字符串，格式 'YYYYMMDDHHmmss'。"""
    return get_now().strftime("%Y%m%d%H%M%S")


def get_now_str_micro() -> str:
    """返回含微秒精度的紧凑时间字符串，可用于生成唯一 ID。

    格式: 'YYYYMMDDHHmmssffffff'
    """
    return get_now().strftime("%Y%m%d%H%M%S%f")
