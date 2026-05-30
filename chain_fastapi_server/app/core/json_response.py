"""JSON 序列化增强模块。

提供 MyEncoder（处理 Decimal / datetime / bytes 等类型）和基于 orjson 的高性能编解码函数。
"""

import json
import decimal
from datetime import datetime, date

import orjson


class MyEncoder(json.JSONEncoder):
    """扩展 JSON 编码器，自动处理 Decimal、datetime、date、bytes 类型。"""

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, bytes):
            return o.decode("utf-8")
        else:
            return super().default(o)


def _orjson_default(o):
    """orjson 的 default 回调，处理 Decimal / datetime / date / bytes。"""
    if isinstance(o, decimal.Decimal):
        return str(o)
    elif isinstance(o, datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(o, date):
        return o.strftime("%Y-%m-%d")
    elif isinstance(o, bytes):
        return o.decode("utf-8")
    raise TypeError


def orjson_dumps(obj, option=None) -> str:
    """使用 orjson 编码为 JSON 字符串。

    遇到超出 64 位范围的大整数时自动回退到 stdlib json.dumps。
    """
    try:
        return orjson.dumps(obj, option=option, default=_orjson_default).decode("utf-8")
    except TypeError as e:
        if "Integer exceeds 64-bit range" in str(e):
            return json.dumps(obj, cls=MyEncoder, ensure_ascii=False)
        raise


def orjson_loads(data):
    """使用 orjson 解码 JSON 数据。"""
    return orjson.loads(data)
