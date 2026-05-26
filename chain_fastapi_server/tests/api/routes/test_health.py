from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_check(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/health")

    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "ok"
    assert content["version"] == settings.VERSION
    assert isinstance(content["pg"], bool)
    assert isinstance(content["mongo"], bool)
    assert isinstance(content["redis"], bool)
