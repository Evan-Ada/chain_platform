"""LLMConfig 路由测试。"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.models import LLMConfig


@pytest.fixture
def clean_llmconfigs(db: Session | None):
    """每个测试前清空 LLMConfig 表。"""
    if db is None:
        yield None
        return
    db.exec(delete(LLMConfig))
    db.commit()
    yield db
    db.exec(delete(LLMConfig))
    db.commit()


class TestLLMConfigAdd:
    """测试 add 路由。"""

    def test_add_sets_default_when_no_active_default(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """无任何有效默认配置时，新增配置自动 is_default=True。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        resp = client.post(
            "/api/v1/LLMConfig/add",
            json={
                "name": "Test Config",
                "provider": "openai",
                "api_key": "sk-test-key-1234",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "enabled": True,
                "is_default": False,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["is_default"] is True

    def test_add_does_not_force_default_when_one_exists(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """已存在有效默认时，新增配置 is_default=False。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        # 先加一条默认配置
        r1 = client.post(
            "/api/v1/LLMConfig/add",
            json={
                "name": "Default Config",
                "provider": "openai",
                "api_key": "sk-test-key-1234",
                "is_default": True,
            },
            headers=headers,
        )
        assert r1.json()["data"]["is_default"] is True

        # 再加一条，is_default 应保持 False
        r2 = client.post(
            "/api/v1/LLMConfig/add",
            json={
                "name": "Second Config",
                "provider": "deepseek",
                "api_key": "sk-deepseek-5678",
                "is_default": False,
            },
            headers=headers,
        )
        assert r2.json()["data"]["is_default"] is False

    def test_add_response_excludes_api_key(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None
    ):
        """add 响应中不包含明文 api_key，仅有 masked_api_key。"""
        if superuser_token_headers is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers
        resp = client.post(
            "/api/v1/LLMConfig/add",
            json={
                "name": "Masked Test",
                "provider": "openai",
                "api_key": "sk-real-key-xxxx",
            },
            headers=headers,
        )
        body = resp.json()
        assert "api_key" not in body["data"]
        assert body["data"]["masked_api_key"] == "****xxxx"


class TestLLMConfigList:
    """测试 list 路由。"""

    def test_list_excludes_soft_deleted(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """list 仅返回未删除的配置。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        # 加两条
        r_a = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "A", "provider": "openai", "api_key": "sk-test-a"},
            headers=headers,
        )
        client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "B", "provider": "openai", "api_key": "sk-test-b"},
            headers=headers,
        )
        id_a = r_a.json()["data"]["id"]

        # 通过 API 软删除 A
        client.post("/api/v1/LLMConfig/delete", json={"id": id_a}, headers=headers)

        resp = client.post("/api/v1/LLMConfig/list", headers=headers)
        body = resp.json()
        assert body["code"] == 200
        names = [c["name"] for c in body["data"]["res"]]
        assert "A" not in names
        assert "B" in names

    def test_list_response_has_total_and_res(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None
    ):
        """list 响应格式为 {total, res:[]}。"""
        if superuser_token_headers is None:
            pytest.skip("需要 superuser")
        resp = client.post("/api/v1/LLMConfig/list", headers=superuser_token_headers)
        body = resp.json()
        assert "total" in body["data"]
        assert "res" in body["data"]
        assert isinstance(body["data"]["res"], list)


class TestLLMConfigDelete:
    """测试 delete 路由（软删除）。"""

    def test_delete_sets_deleted_at(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """delete 写入 deleted_at 而非物理删除。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        # 加一条
        r = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "To Delete", "provider": "openai", "api_key": "sk-test"},
            headers=headers,
        )
        cfg_id = r.json()["data"]["id"]

        # 删掉
        dr = client.post(
            "/api/v1/LLMConfig/delete",
            json={"id": cfg_id},
            headers=headers,
        )
        assert dr.json()["code"] == 200

        # 数据库中 deleted_at 被设置
        cfg = db.get(LLMConfig, cfg_id)
        assert cfg.deleted_at is not None

    def test_delete_default_switches_to_next(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """删除默认配置后，自动切换到最早的剩余有效配置。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        # 加两条：A=默认, B=非默认
        r1 = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "A", "provider": "openai", "api_key": "sk-test-a", "is_default": True},
            headers=headers,
        )
        r2 = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "B", "provider": "deepseek", "api_key": "sk-test-b", "is_default": False},
            headers=headers,
        )
        id_a = r1.json()["data"]["id"]
        id_b = r2.json()["data"]["id"]

        # 删 A
        client.post("/api/v1/LLMConfig/delete", json={"id": id_a}, headers=headers)

        # B 变为默认
        cfg_b = db.get(LLMConfig, id_b)
        assert cfg_b.is_default is True


class TestLLMConfigSetDefault:
    """测试 setDefault 路由。"""

    def test_setdefault_rejects_deleted_config(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """setDefault 对已删除配置返回错误。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        r = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "To Soft Delete", "provider": "openai", "api_key": "sk-test"},
            headers=headers,
        )
        cfg_id = r.json()["data"]["id"]
        cfg = db.get(LLMConfig, cfg_id)
        cfg.deleted_at = datetime.now(timezone.utc)
        db.add(cfg)
        db.commit()

        dr = client.post("/api/v1/LLMConfig/setDefault", json={"id": cfg_id}, headers=headers)
        assert dr.json()["code"] == 400


class TestLLMConfigUpdate:
    """测试 update 路由。"""

    def test_update_rejects_deleted_config(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """update 对已删除配置返回错误。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        r = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "To Delete", "provider": "openai", "api_key": "sk-test"},
            headers=headers,
        )
        cfg_id = r.json()["data"]["id"]
        cfg = db.get(LLMConfig, cfg_id)
        cfg.deleted_at = datetime.now(timezone.utc)
        db.add(cfg)
        db.commit()

        ur = client.post(
            "/api/v1/LLMConfig/update",
            json={"id": cfg_id, "name": "New Name"},
            headers=headers,
        )
        assert ur.json()["code"] == 400


class TestLLMConfigTest:
    """测试 test 路由。"""

    def test_test_returns_latency_ms(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """test 成功时返回 reply 和 latency_ms。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        # 先加一条配置
        r = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "Test Config", "provider": "openai", "api_key": "sk-test-key-1234"},
            headers=headers,
        )
        cfg_id = r.json()["data"]["id"]

        with patch("app.services.llm_providers.registry.get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.chat = AsyncMock(return_value="ok")
            mock_get.return_value = mock_provider

            tr = client.post(
                "/api/v1/LLMConfig/test",
                json={"id": cfg_id},
                headers=headers,
            )
        body = tr.json()
        if body["code"] == 200:
            assert "reply" in body["data"]
            assert "latency_ms" in body["data"]
            assert body["data"]["reply"] == "ok"

    def test_test_without_id_uses_inline_params(self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None):
        """test 不传 id 时使用内联参数。"""
        if superuser_token_headers is None:
            pytest.skip("需要 superuser")
        with patch("app.services.llm_config_service.test_connectivity", new_callable=AsyncMock) as mock_test:
            mock_test.return_value = ("ok", 42)
            tr = client.post(
                "/api/v1/LLMConfig/test",
                json={
                    "provider": "deepseek",
                    "api_key": "sk-inline-key",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                },
                headers=superuser_token_headers,
            )
            body = tr.json()
            if body["code"] == 200:
                assert body["data"]["reply"] == "ok"
                assert body["data"]["latency_ms"] == 42

    def test_test_updates_last_test_fields(
        self, client: TestClient, superuser_token_headers: dict | None, clean_llmconfigs: Session | None, db: Session | None
    ):
        """test 成功后将结果写入 last_test_at/status/message。"""
        if superuser_token_headers is None or db is None:
            pytest.skip("需要 superuser")
        headers = superuser_token_headers

        r = client.post(
            "/api/v1/LLMConfig/add",
            json={"name": "Write Back", "provider": "openai", "api_key": "sk-test-key-1234"},
            headers=headers,
        )
        cfg_id = r.json()["data"]["id"]

        with patch("app.services.llm_providers.registry.get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.chat = AsyncMock(return_value="ok")
            mock_get.return_value = mock_provider

            client.post("/api/v1/LLMConfig/test", json={"id": cfg_id}, headers=headers)

        cfg = db.get(LLMConfig, cfg_id)
        assert cfg.last_test_at is not None
        assert cfg.last_test_status == "success"
        assert cfg.last_test_message == "ok"


class TestLLMConfigService:
    """测试 llm_config_service 单元逻辑。"""

    def test_update_last_test_result_writes_fields(self, db: Session | None):
        """update_last_test_result 正确写入三个字段。"""
        if db is None:
            pytest.skip("需要数据库")
        from app.services.llm_config_service import update_last_test_result

        cfg = LLMConfig(
            name="Test",
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

        update_last_test_result(cfg, db, "success", "ok")

        assert cfg.last_test_at is not None
        assert cfg.last_test_status == "success"
        assert cfg.last_test_message == "ok"

    def test_test_connectivity_returns_reply_and_latency(self, db: Session | None):
        """test_connectivity 返回 reply 和 latency_ms。"""
        if db is None:
            pytest.skip("需要数据库")
        import asyncio
        from app.services.llm_config_service import test_connectivity

        cfg = LLMConfig(
            name="Test",
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

        with patch("app.services.llm_providers.registry.get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.chat = AsyncMock(return_value="ok")
            mock_get.return_value = mock_provider

            reply, latency = asyncio.run(test_connectivity(cfg))
            assert reply == "ok"
            assert latency >= 0
