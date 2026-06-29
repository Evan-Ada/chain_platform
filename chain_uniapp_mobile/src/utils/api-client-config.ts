// API 请求工具函数
// 使用 uni.request 实现,避免 Windows ESM 路径问题

const BASE_URL = import.meta.env.VITE_SERVER_BASEURL || 'http://localhost:8009'

/**
 * 发送 HTTP 请求
 */
export function request<T = any>(options: {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  data?: any
  headers?: Record<string, string>
}): Promise<{
  data: T
  status: number
}> {
  return new Promise((resolve, reject) => {
    // 从本地存储获取 token
    const token = uni.getStorageSync('token')

    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    // 如果有 token,添加到请求头
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: headers,
      success: (res) => {
        resolve({
          data: res.data as T,
          status: res.statusCode,
        })
      },
      fail: (err) => {
        reject(err)
      },
    })
  })
}

/**
 * POST 请求
 */
export function post<T = any>(url: string, data?: any): Promise<{ data: T; status: number }> {
  return request<T>({ url, method: 'POST', data })
}

/**
 * GET 请求
 */
export function get<T = any>(url: string, params?: Record<string, any>): Promise<{ data: T; status: number }> {
  // 将参数拼接到 URL
  let finalUrl = url
  if (params) {
    const searchParams = new URLSearchParams()
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        searchParams.append(key, String(params[key]))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      finalUrl += `?${queryString}`
    }
  }

  return request<T>({ url: finalUrl, method: 'GET' })
}

console.log(`API 请求工具已加载,BaseURL: ${BASE_URL}`)
