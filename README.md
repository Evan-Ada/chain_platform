# chain_platform

Chain 系列业务**单仓库 monorepo**，作为各二开项目的代码基座。

## 子目录

| 目录 | 技术栈 | 说明 |
|------|--------|------|
| [`chain_fastapi_server`](chain_fastapi_server/) | FastAPI | 后端 API（占位，后续脚手架） |
| [`chain_web_admin`](chain_web_admin/) | Vue 3 + Vite | PC Web / 管理端（占位） |
| [`chain_uniapp_mobile`](chain_uniapp_mobile/) | UniApp + Vue 3 | App 与微信小程序（占位） |

## 数据层（规划）

- MySQL 或 MongoDB
- Redis

配置与密钥放在各子目录的 `.env`（勿提交），参考各子目录后续提供的 `.env.example`。

## 二开新项目

1. Fork 本仓库或复制 monorepo 结构。
2. 在父工作区通过 Git submodule 引用固定 commit。
3. 按业务重命名包目录或保留 `chain_*` 前缀统一升级基座。

## 父工作区

通常由 [`demo_workspace`](../) 等元仓库以 submodule 方式引用本仓库，并与 `meridian_workspace`（AI/Cursor 配置）并列。
