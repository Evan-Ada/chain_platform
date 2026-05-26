# chain_uniapp_mobile

Chain platform 移动端：基于 [unibest](https://github.com/codercup/unibest) 模板（UniApp + Vue3 + TS + Pinia + UnoCSS + uni-ui），同一份代码输出 H5 / iOS App / Android App / 微信小程序等。

## 本地开发

```bash
pnpm install              # 模板强制使用 pnpm（preinstall 钩子限制）
pnpm dev:h5               # 浏览器端调试，默认 http://localhost:5174
pnpm dev:mp-weixin        # 微信小程序，用微信开发者工具打开 dist/dev/mp-weixin
pnpm dev:app              # App（需要 HBuilderX 或 cli-android/ios）
```

> 端口固定为 **5174**，避开 `chain_web_admin` 的 5173。如需修改请编辑 `env/.env` 中的 `VITE_APP_PORT`。

后端 baseURL 在 `env/.env.development` 的 `VITE_SERVER_BASEURL`（unibest 原生变量）以及跨 Agent 约定别名 `VITE_API_URL`，默认指向 `http://localhost:8000`。根目录 `.env.example` 是面向跨子 Agent 接口约定的占位说明；真实生效的环境文件位于 `env/` 子目录。

## API 客户端

业务请求**优先从 `@chain/api-client` 引入**（共享包，由后端 OpenAPI 自动生成；运行 `node scripts/sync-openapi.mjs` 更新）。`src/http/` 与 `src/api/` 下的手写请求仅用于 unibest 模板示例与平台特有 API（如 `uni.getSystemInfo`）；共享包就绪后将由主 Agent 收口替换。

## 平台条件编译

- `// #ifdef MP-WEIXIN ... // #endif` 微信小程序专属
- `// #ifdef APP-PLUS ... // #endif` App 端专属
- `// #ifdef H5 ... // #endif` H5 专属

## 目录约定

- `src/pages/`：页面（由 `@uni-helper/vite-plugin-uni-pages` 自动生成 `pages.json`）
- `src/components/`：自动按需注册的组件
- `src/api/` / `src/http/`：网络请求封装（详见上文 API 客户端约定）
- `src/store/`：Pinia 状态
- `manifest.config.ts`：UniApp manifest（编译为 `src/manifest.json`，已 gitignore）
- `pages.config.ts`：页面配置补充
- `env/`：分环境变量（`.env` / `.env.development` / `.env.production` / `.env.test`）

更完整说明详见 [unibest 官方文档](https://unibest.tech/)。
