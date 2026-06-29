// unwrapResult：把新 SDK 的 RequestResult 拆成 data 或抛错。
// 业务侧应当用：
//   const { data } = await unwrapResult(usersReadUserMe({}))
//
// 这样 handleError / QueryClient 拿到的就是普通 Error（旧 ApiError 形状），
// 旧 utils.ts 的 extractErrorMessage 能正常读 err.body.detail。
import { ApiError } from "@/lib/apiError"

type FieldResult<TData> = {
  data?: TData
  error?: unknown
  request?: Request
  response?: Response
}

function toApiError(err: unknown, response?: Response): Error {
  if (err instanceof Error) return err
  if (response) {
    return new ApiError({
      status: response.status,
      statusText: response.statusText,
      body: err,
      response,
      message:
        err && typeof err === "object" && "detail" in err
          ? String((err as { detail: unknown }).detail)
          : `HTTP ${response.status} ${response.statusText}`,
    })
  }
  if (err && typeof err === "object") {
    return new ApiError({
      status: 0,
      body: err,
      message: "Unknown error",
    })
  }
  return new ApiError({ status: 0, message: String(err) })
}

export async function unwrapResult<TData>(
  promise: Promise<FieldResult<TData>>,
): Promise<TData> {
  const result = await promise
  if (result.error !== undefined) {
    throw toApiError(result.error, result.response)
  }
  return result.data as TData
}

/** 解析后端 resp_200 信封 `{ code, msg, data }`，返回内层 data。 */
export function extractApiData<T>(body: unknown): T {
  if (
    body &&
    typeof body === "object" &&
    "code" in body &&
    "data" in body
  ) {
    return (body as { data: T }).data
  }
  return body as T
}

export async function unwrapApiData<TData>(
  promise: Promise<FieldResult<unknown>>,
): Promise<TData> {
  const body = await unwrapResult<unknown>(promise)
  return extractApiData<TData>(body)
}