# chain-fastapi-server

Chain 平台的 FastAPI 后端，基于 [Tiangolo full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 落地，加入 MongoDB / Redis 占位与统一 `/health` 健康检查。

## 技术栈

- **FastAPI** + **SQLModel** + **Alembic**：HTTP API、ORM 与数据库迁移。
- **PostgreSQL**：主关系库（用户、业务表）。
- **MongoDB** (motor)：非结构化数据（日志、画像、文档型业务）。
- **Redis** (redis.asyncio)：缓存、限流、任务队列。
- **Pydantic v2 / pydantic-settings**：配置与数据校验。
- **PyJWT + pwdlib**：JWT 鉴权与密码哈希。
- **uv**：包管理与虚拟环境。

## 目录结构

```
chain_fastapi_server/
├── app/
│   ├── api/
│   │   ├── deps.py           # 依赖注入（Session、当前用户等）
│   │   ├── main.py           # 路由聚合（含 health）
│   │   └── routes/           # 业务路由：login / users / items / utils / health / private
│   ├── alembic/              # 数据库迁移脚本
│   ├── core/
│   │   ├── config.py         # Settings（含 MONGO_URL / REDIS_URL）
│   │   ├── db.py             # PostgreSQL 引擎与会话
│   │   ├── mongo.py          # Mongo 异步连接占位
│   │   ├── redis.py          # Redis 异步连接占位
│   │   └── security.py       # JWT / 密码哈希
│   ├── crud.py
│   ├── main.py               # FastAPI 应用入口
│   ├── models.py             # SQLModel 模型
│   └── email-templates/      # 邮件模板
├── tests/                    # pytest 测试
├── scripts/                  # 启动 / 测试脚本
├── alembic.ini
├── pyproject.toml
├── Dockerfile
└── .env.example
```

## 本地启动

```bash
cp .env.example .env       # 复制并按需修改连接串、密钥
uv sync                    # 安装依赖到 .venv
uv run uvicorn app.main:app --reload --port 8000
```

- 默认端口：`8000`
- OpenAPI：`http://localhost:8000/api/v1/openapi.json`
- Swagger UI：`http://localhost:8000/docs`

## 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

返回示例：

```json
{ "status": "ok", "pg": true, "mongo": false, "redis": false }
```

- `pg` / `mongo` / `redis` 表示各依赖的实际连通性。
- 未配置 `MONGO_URL` / `REDIS_URL` 时返回 `false`，**不影响应用启动**。

## 数据库迁移

```bash
uv run alembic upgrade head             # 应用迁移
uv run alembic revision --autogenerate  # 生成新迁移
```

## 测试

```bash
uv run pytest                # 单元 / 集成测试
bash scripts/test.sh         # 含覆盖率
```

## 提示

- 请把 `.env.example` 复制为 `.env` 后填入真实值；切勿把 `.env` 提交到仓库。
- 修改 / 新增 API 后，请同步更新 `.ai/context/api_docs.md`，并通知前端运行 `node scripts/sync-openapi.mjs` 重新生成客户端。
