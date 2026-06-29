from sqlalchemy import text

from app.core.db import engine

with engine.begin() as conn:
    conn.execute(text("DELETE FROM alembic_version"))
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('fe56fa70289e')"))
print("alembic stamped fe56fa70289e")
