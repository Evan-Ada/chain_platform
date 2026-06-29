import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      // 统一指向 packages 共享客户端（@hey-api/openapi-ts 生成的新风格 SDK），
      // 旧的 chain_web_admin/src/client/ 目录不再使用。
      "@chain/api-client": path.resolve(
        __dirname,
        "../packages/shared-api-client/src",
      ),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
})
