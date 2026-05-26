# @chain/api-client

OpenAPI 自动生成的 TypeScript 客户端，Web React 与 Mobile UniApp 共用。

## 生成

```bash
node scripts/sync-openapi.mjs
```

## 严禁手工修改

`src/` 下所有文件由生成器写入。改动应通过：

1. 在 `chain_fastapi_server/` 修改 FastAPI schema / 路由
2. 启动后端
3. 重新跑 `node scripts/sync-openapi.mjs`

详见 [.cursor/rules/openapi-client-sync.mdc](../../../.cursor/rules/openapi-client-sync.mdc)。
