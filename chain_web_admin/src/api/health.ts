// 直连后端 health 接口,不走 packages 客户端,方便轻量探活。
// 端口从 import.meta.env.VITE_API_URL 推断(去掉 /api/v1 后缀)。
export type HealthStatus = {
  status: "ok"
  pg: boolean
  mongo: boolean
  redis: boolean
  version: string
}

function getApiBaseUrl(): string {
  const raw = (import.meta.env.VITE_API_URL as string | undefined) || ""
  return raw.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "")
}

export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/health`)

  if (!response.ok) {
    throw new Error("Failed to load health status")
  }

  return response.json() as Promise<HealthStatus>
}