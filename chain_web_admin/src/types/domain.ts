/** 后端 resp_200 路由返回的字典形状（OpenAPI 未标注 response_model）。 */

export type ListEnvelope<T> = { total: number; res: T[] }

export type SubscriptionItem = {
  id: number
  user_id: number
  name: string
  keywords: string[]
  sources: string[]
  schedule_type: string
  schedule_cron: string
  enabled: boolean
  last_run_at?: string | null
  created_at?: string | null
}

export type DataSourceConfigItem = {
  id: number
  name: string
  source_type: string
  enabled: boolean
  config: Record<string, unknown>
  created_at?: string | null
}

export type ScheduledTaskItem = {
  id: number
  name: string
  biz_type: string
  biz_id?: number | null
  cron_expr: string
  enabled: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  owner_user_id: number
  created_at?: string | null
}

export type LlmConfigItem = {
  id: number
  name: string
  provider: string
  base_url: string
  model: string
  enabled: boolean
  is_default: boolean
  masked_api_key: string
  extra?: Record<string, unknown>
  last_test_at?: string | null
  last_test_status?: string | null
  last_test_message?: string | null
  created_at?: string | null
}
