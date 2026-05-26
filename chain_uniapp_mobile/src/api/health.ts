export interface HealthStatus {
  status: 'ok'
  pg: boolean
  mongo: boolean
  redis: boolean
  version: string
}

function isHealthStatus(data: unknown): data is HealthStatus {
  if (!data || typeof data !== 'object') {
    return false
  }

  const health = data as Partial<HealthStatus>
  return (
    health.status === 'ok'
    && typeof health.pg === 'boolean'
    && typeof health.mongo === 'boolean'
    && typeof health.redis === 'boolean'
    && typeof health.version === 'string'
  )
}

export function getHealthStatus() {
  return new Promise<HealthStatus>((resolve, reject) => {
    uni.request({
      url: '/api/v1/health',
      method: 'GET',
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300 && isHealthStatus(res.data)) {
          resolve(res.data)
          return
        }

        reject(new Error('Invalid health status response'))
      },
      fail: reject,
    })
  })
}
