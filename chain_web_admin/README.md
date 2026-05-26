# chain-web-admin

Chain 平台的 Web 管理端，基于 [Tiangolo full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) 的 React 19 模板落地，按需替换 API 客户端来源为共享包 `@chain/api-client`。

## 技术栈

- **React 19** + **TypeScript** + **Vite 7**：现代化前端构建。
- **TanStack Router** + **TanStack Query**：文件式路由 + 服务端数据缓存。
- **TanStack Table**：表格能力。
- **Tailwind CSS v4** + **shadcn/ui** + **Radix UI**：原子化样式与无障碍组件。
- **React Hook Form** + **Zod**：表单与 Schema 校验。
- **Axios**：HTTP 通信。
- **Biome**：格式化与 lint。
- **Playwright**：端到端测试。
- **@hey-api/openapi-ts**：从后端 OpenAPI 生成 TS 客户端。

## 本地启动

```bash
cp .env.example .env       # 复制环境变量；VITE_API_URL 默认指向 http://localhost:8000
npm install                # 安装依赖
npm run dev                # 启动开发服务器（默认端口 5173）
```

访问：`http://localhost:5173`

## API 客户端来源

> **API 客户端不在本仓库下手写。** 所有调用后端 `/api/v1/**` 的 TS 客户端均来自仓库内共享包 `@chain/api-client`（路径：`chain_platform/packages/shared-api-client`）。

- 客户端代码由 **`node scripts/sync-openapi.mjs`**（仓库根/`chain_platform` 维护）从后端 `http://localhost:8000/api/v1/openapi.json` 自动生成。
- 本目录的 `openapi-ts.config.ts` 已把 `output` 指向 `../packages/shared-api-client/src/`，因此 `npm run generate-client` 会写入共享包，而不是本目录的 `src/client/`。
- 在业务代码中按下面方式使用：

  ```ts
  import { LoginService, UsersService } from "@chain/api-client";
  ```

- 后端 OpenAPI 变化后请运行同步脚本，并提交共享包 `dist/` 的变更（如果共享包采用预构建发布）。

## 常用脚本

```bash
npm run dev               # 开发模式（端口 5173）
npm run build             # 构建产物
npm run lint              # Biome 检查 + 自动修复
npm run preview           # 预览构建产物
npm run generate-client   # 从后端 OpenAPI 重新生成共享 client（输出到 packages/shared-api-client/src）
npm test                  # Playwright E2E
npm run test:ui           # Playwright UI 模式
```

## 跨服务对齐

- 后端默认端口：**8000**，OpenAPI：`http://localhost:8000/api/v1/openapi.json`。
- 本前端默认端口：**5173**。
- `.env` 中 `VITE_API_URL` 不要带尾斜杠。

## 提示

- `src/client/` 仍保留 Tiangolo 模板生成的样例，仅作历史参考；新业务请统一切换到 `@chain/api-client`。
- 修改 / 新增前端可见的 API 后，请先让后端更新 `/api/v1/openapi.json`，再运行 `node scripts/sync-openapi.mjs` 同步共享包。
