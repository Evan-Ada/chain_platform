// Web 端 API 客户端引导：在 main.tsx 顶部最早被 import。
//
// - 用 packages/shared-api-client 已经生成的 fetch client，
//   把它替换成读自 VITE_API_URL 的 baseUrl。
// - 注册 request 拦截器，自动从 localStorage 注入 Bearer token。
// - 注册 error 拦截器，在 401/403 时清 token 并跳登录页。
//
// 注意：packages/src/index.ts 会在导入时立刻跑一次
//   const client = createClient(createConfig({ baseUrl: 'http://localhost:8009' }))
// 因此我们必须在引用任何业务函数前 import 这个文件，并立刻 setConfig 覆盖。
// 由于 index.ts 是生成器产物，不暴露 client 实例，我们从 client.gen 直拿。
import { client } from "@chain/api-client/client.gen"

const apiBaseUrl =
  (import.meta.env.VITE_API_URL as string | undefined) ||
  "http://localhost:8009/api/v1"

client.setConfig({
  baseUrl: apiBaseUrl,
  throwOnError: false,
})

client.interceptors.request.use((request: Request) => {
  const token = localStorage.getItem("access_token")
  if (token) {
    request.headers.set("Authorization", `Bearer ${token}`)
  }
  return request
})

client.interceptors.error.use((error: unknown) => {
  if (
    error &&
    typeof error === "object" &&
    "status" in error &&
    typeof (error as { status?: unknown }).status === "number" &&
    [401, 403].includes((error as { status: number }).status)
  ) {
    localStorage.removeItem("access_token")
    if (
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.href = "/login"
    }
  }
  return error
})

/**
 * 处理 API 响应：检查 401/403 并跳转登录页。
 * 用于原生 fetch 包装，确保和 SDK client 一样的错误处理逻辑。
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if ([401, 403].includes(response.status)) {
    localStorage.removeItem("access_token")
    if (
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.href = "/login"
    }
    throw new Error(`HTTP ${response.status} ${response.statusText}`)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = body.detail || `HTTP ${response.status} ${response.statusText}`
    throw new Error(message)
  }
  return response.json()
}

/**
 * 封装的 fetch，确保自动附加 Authorization header 并处理 401/403。
 */
export async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("access_token")
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const fullUrl = url.startsWith("http") ? url : `${apiBaseUrl}${url}`
  const response = await fetch(fullUrl, { ...options, headers })

  if ([401, 403].includes(response.status)) {
    localStorage.removeItem("access_token")
    if (
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.href = "/login"
    }
    throw new Error(`HTTP ${response.status} ${response.statusText}`)
  }

  return handleApiResponse<T>(response)
}