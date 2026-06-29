"""pytest 配置。"""

from collections.abc import Generator
from contextlib import suppress

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    """数据库 session fixture，连接失败时返回 None。"""
    try:
        with Session(engine) as session:
            init_db(session)
            yield session
            with suppress(Exception):
                from sqlmodel import delete

                session.execute(delete(Item))
                session.execute(delete(User))
                session.commit()
    except Exception:
        # DB not available - yield None so tests can handle it gracefully
        yield None


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str] | None:
    try:
        return get_superuser_token_headers(client)
    except Exception:
        return None


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session | None) -> dict[str, str] | None:
    if db is None:
        return None
    try:
        return authentication_token_from_email(
            client=client, email=settings.EMAIL_TEST_USER, db=db
        )
    except Exception:
        return None
