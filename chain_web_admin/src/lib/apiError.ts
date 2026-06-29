// ApiError 适配层：把新 SDK 返回的 `error` 形状包成旧的 ApiError 类。
// 主要给旧 `utils.ts -> handleError` 用，业务调用方拿到的是新 SDK 字段
// `{ data, error, request, response }`。
export class ApiError extends Error {
  status: number
  statusText: string
  body: unknown
  request?: Request
  response?: Response

  constructor(opts: {
    status: number
    statusText?: string
    body?: unknown
    request?: Request
    response?: Response
    message?: string
  }) {
    super(opts.message ?? `HTTP ${opts.status} ${opts.statusText ?? ""}`)
    this.name = "ApiError"
    this.status = opts.status
    this.statusText = opts.statusText ?? ""
    this.body = opts.body
    this.request = opts.request
    this.response = opts.response
  }
}