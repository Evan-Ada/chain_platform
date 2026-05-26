import { OpenAPI } from "@/client"

export type HealthStatus = {
  status: "ok"
  pg: boolean
  mongo: boolean
  redis: boolean
  version: string
}

export async function getHealthStatus(): Promise<HealthStatus> {
  const baseUrl = OpenAPI.BASE.replace(/\/$/, "")
  const response = await fetch(`${baseUrl}/api/v1/health`)

  if (!response.ok) {
    throw new Error("Failed to load health status")
  }

  return response.json() as Promise<HealthStatus>
}
