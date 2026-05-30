"""动态 WHERE 子句构建器。

根据条件配置列表和请求数据，动态生成 SQL WHERE 子句及参数字典。
适配 PostgreSQL（find_in_set 改用 ANY(string_to_array(...))）。
"""

from typing import Any


def not_empty(data: dict, field: str) -> bool:
    """字段存在且不为 falsy 值（0、空字符串、空列表、空字典等均视为"空"）。"""
    return field in data and bool(data[field])


def not_none(data: dict, field: str) -> bool:
    """字段存在且不为 None（0、空字符串等视为有效值）。"""
    return field in data and data[field] is not None


# 规则名称 -> 检查函数映射
_RULE_MAP = {
    "notEmpty": not_empty,
    "notNone": not_none,
}


def _build_condition(
    abbr: str,
    field: str,
    rule: str,
    operator: str,
    data: dict,
    alias: str | None = None,
) -> dict:
    """根据单条条件配置生成 SQL 片段和参数。"""
    post_field = alias or field
    check_fn = _RULE_MAP.get(rule)
    if check_fn is None or not check_fn(data, post_field):
        return {"where": "", "value": {}}

    where = ""
    value: dict[str, Any] = {}

    if operator == "equal":
        where = f" AND {abbr}.{field} = :{post_field}"
        value = {post_field: data[post_field]}

    elif operator == "like":
        where = f" AND {abbr}.{field} LIKE :{post_field}"
        value = {post_field: f"%{data[post_field]}%"}

    elif operator == "likeor":
        like_fields = field.split(",")
        like_abbrs = abbr.split(",")
        parts = []
        for i, lf in enumerate(like_fields):
            a = like_abbrs[i] if i < len(like_abbrs) else abbr
            parts.append(f"{a}.{lf} LIKE :{post_field}")
        where = f" AND ({' OR '.join(parts)})"
        value = {post_field: f"%{data[post_field]}%"}

    elif operator == "ge":
        where = f" AND {abbr}.{field} >= :{post_field}"
        value = {post_field: data[post_field]}

    elif operator == "gt":
        where = f" AND {abbr}.{field} > :{post_field}"
        value = {post_field: data[post_field]}

    elif operator == "le":
        where = f" AND {abbr}.{field} <= :{post_field}"
        value = {post_field: data[post_field]}

    elif operator == "lt":
        where = f" AND {abbr}.{field} < :{post_field}"
        value = {post_field: data[post_field]}

    elif operator == "in":
        # PostgreSQL 适配：find_in_set -> ANY(string_to_array(...))
        where = f" AND {post_field} = ANY(string_to_array({abbr}.{field}, ','))"
        value = {post_field: str(data[post_field])}

    elif operator == "not_in":
        # PostgreSQL 适配：使用 != ALL(ARRAY[...]) 替代 NOT IN
        in_values = data[post_field]
        if isinstance(in_values, (list, tuple)):
            placeholders = [f":{post_field}_{i}" for i in range(len(in_values))]
            where = f" AND {abbr}.{field} NOT IN ({', '.join(placeholders)})"
            value = {f"{post_field}_{i}": v for i, v in enumerate(in_values)}
        else:
            where = f" AND {abbr}.{field} != :{post_field}"
            value = {post_field: in_values}

    return {"where": where, "value": value}


def rearrange_sql(data: dict, condition_arr: list[dict]) -> dict:
    """根据条件配置列表重组 SQL WHERE 子句。

    Args:
        data: 请求参数字典。
        condition_arr: 条件配置列表，每项包含:
            - abbr: 表别名（如 "t"）
            - field: 字段名
            - rule: 校验规则（"notEmpty" 或 "notNone"）
            - operator: 操作符（equal / like / likeor / ge / gt / le / lt / in / not_in）
            - alias: （可选）参数别名

    Returns:
        {"where": " AND ...", "value": {param: value, ...}}
    """
    query: dict[str, Any] = {"where": " 1=1 ", "value": {}}

    for c in condition_arr:
        result = _build_condition(
            abbr=c["abbr"],
            field=c["field"],
            rule=c["rule"],
            operator=c["operator"],
            data=data,
            alias=c.get("alias"),
        )

        if result["where"]:
            query["where"] += result["where"]
            query["value"].update(result["value"])

    return query
