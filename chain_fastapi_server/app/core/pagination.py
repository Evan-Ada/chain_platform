"""分页查询模块。

提供通用分页函数，使用 PostgreSQL LIMIT/OFFSET 语法。
依赖 fastapi_sqlalchemy 的 db.session。
"""

from sqlalchemy import text
from fastapi_sqlalchemy import db


def paginate(
    query: dict,
    total_sql: str,
    main_sql: str,
    page_num: int,
    page_size: int,
    has_group_by: bool = False,
) -> dict:
    """通用分页查询，返回 {"total": N, "res": [...]}。

    Args:
        query: 由 rearrange_sql 返回的查询字典，包含 "where" 和 "value"。
        total_sql: 计算总记录数的 SQL（需包含 WHERE 条件占位）。
        main_sql: 主查询 SQL（不含 LIMIT/OFFSET）。
        page_num: 页码（从 1 开始）。
        page_size: 每页条数。
        has_group_by: 是否有 GROUP BY（有则用行数代替 COUNT）。

    Returns:
        {"total": 总记录数, "res": 当前页数据列表}
    """
    params = dict(query["value"])

    # 计算总记录数
    total = _get_total(total_sql, params, has_group_by)

    # 拼接 LIMIT/OFFSET（PostgreSQL 语法）
    offset = (page_num - 1) * page_size
    paged_sql = f"{main_sql} LIMIT :_limit OFFSET :_offset"
    params["_limit"] = page_size
    params["_offset"] = offset

    res = _execute_query(paged_sql, params)

    return {"total": total, "res": res}


def _get_total(total_sql: str, params: dict, has_group_by: bool) -> int:
    """获取总记录数。"""
    rp = db.session.execute(text(total_sql), params)
    rows = [dict(r) for r in rp.mappings()]

    if not has_group_by:
        return rows[0]["total"] if rows else 0
    return len(rows)


def _execute_query(sql: str, params: dict) -> list[dict]:
    """执行查询并返回字典列表。"""
    rp = db.session.execute(text(sql), params)
    return [dict(r) for r in rp.mappings()]
