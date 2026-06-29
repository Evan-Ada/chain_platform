/**
 * 洞见 API 封装
 * 注意：由于 @chain/api-client 可能尚未生成，使用 fetch 直接调用
 */

const BASE_URL = import.meta.env.VITE_SERVER_BASEURL || 'http://localhost:8009'

function getToken(): string {
  return uni.getStorageSync('token') || ''
}

async function request<T = any>(options: {
  url: string
  method?: string
  data?: any
}): Promise<{ data: T }> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await new Promise<any>((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'POST',
      data: options.data,
      header: headers,
      success: (r: any) => resolve(r.data),
      fail: (err: any) => reject(err),
    })
  })
  return { data: res }
}

export interface InsightItem {
  id: number
  user_id: number
  source_type: string
  raw_text: string
  ai_interpretation: {
    core_viewpoint?: string
    emotional_tone?: string
    motivation?: string
    actionable_suggestions?: string[]
    tags?: string[]
    reflection_questions?: string[]
  }
  tags: string[]
  status: 'pending' | 'done' | 'failed'
  error_message?: string
  parent_id?: number
  linked_digest_id?: number
  created_at: string
  updated_at: string
  follow_ups?: InsightItem[]
}

export const insightApi = {
  /** 提交洞见 */
  add(raw_text: string, tags: string[] = []) {
    return request<InsightItem>({
      url: '/api/v1/Insight/add',
      data: { raw_text, tags, source_type: 'manual_text' },
    })
  },

  /** 列表 */
  list(params: {
    tag?: string
    status?: string
    page_num?: number
    page_size?: number
  }) {
    return request<{ total: number; res: InsightItem[] }>({
      url: '/api/v1/Insight/list',
      data: { page_num: 1, page_size: 50, ...params },
    })
  },

  /** 详情 */
  get(id: number) {
    return request<InsightItem>({
      url: '/api/v1/Insight/get',
      data: { id },
    })
  },

  /** 追问 */
  followUp(parent_id: number, raw_text: string) {
    return request<InsightItem>({
      url: '/api/v1/Insight/followUp',
      data: { parent_id, raw_text },
    })
  },

  /** 更新标签 */
  updateTags(id: number, tags: string[]) {
    return request<InsightItem>({
      url: '/api/v1/Insight/updateTags',
      data: { id, tags },
    })
  },

  /** 删除 */
  delete(id: number) {
    return request<void>({
      url: '/api/v1/Insight/delete',
      data: { id },
    })
  },
}
