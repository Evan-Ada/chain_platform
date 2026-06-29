# chain_platform CI 占位

当前所有工作流默认 `workflow_dispatch`（手动触发），便于在云端环境就绪前不消耗 Actions 额度。

| 文件 | 包含 jobs | 启用方式 |
|---|---|---|
| `tests.yml` | `test-backend` / `test-web` / `test-mobile` / `openapi-drift` | 把 `on:` 改回 `pull_request:` + `push:` |

## 本地等价

| Job | 本地命令 | 工作目录 |
|---|---|---|
| `test-backend` | `uv run pytest` | `chain_platform/chain_fastapi_server/` |
| `test-web` (lint) | `npm run lint` | `chain_platform/chain_web_admin/` |
| `test-web` (e2e) | `npm run test:e2e` | `chain_platform/chain_web_admin/`（需后端在线） |
| `test-mobile` (type) | `npm run type-check` | `chain_platform/chain_uniapp_mobile/` |
| `openapi-drift` | `node scripts/sync-openapi.mjs` 后 `git status` 应干净 | 父根 |

## 后续推荐扩展（按重要性）

1. 把 Tiangolo 模板的 `playwright.yml` + `test-docker-compose.yml` 适配进来（参考 https://github.com/tiangolo/full-stack-fastapi-template）
2. 加 `dependabot.yml`（npm + pip + GitHub Actions 三套）
3. 加 `pre-commit.yml`（统一 lint/format gate）
4. 加 `release.yml`（按 tag 触发 docker build & push）

父级 AI 治理 CI 见 `demo_workspace/.github/workflows/ai-baseline.yml`（只跑 AI 资产 + 提交信息检查）。
