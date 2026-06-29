"""重建订阅/推送相关表为 Integer 自增主键（对齐 a7f0c1b9d2e3 迁移）。"""

from sqlalchemy import text

from app.core.db import engine

DROP_ORDER = [
    "pushmessage",
    "contentrecord",
    "subscription",
    "scheduledtask",
    "tagsynonym",
    "tag",
    "datasourceconfig",
    "llmconfig",
    "pushpreference",
    "userdevice",
]


def rebuild() -> None:
    with engine.begin() as conn:
        for table in DROP_ORDER:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
    print("已删除旧 UUID 表，请执行: uv run alembic stamp fe56fa70289e && uv run alembic upgrade head")


if __name__ == "__main__":
    rebuild()
