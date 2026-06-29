import { ApiError } from "@/lib/apiError"

function extractErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message

  if (err instanceof ApiError) {
    const detail = (err.body as { detail?: unknown } | undefined)?.detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first && typeof first === "object" && "msg" in first) {
        return String((first as { msg: unknown }).msg)
      }
    }
    if (typeof detail === "string" && detail) return detail
    return "Something went wrong."
  }

  if (err && typeof err === "object") {
    const detail =
      (err as { body?: { detail?: unknown }; detail?: unknown }).body?.detail ??
      (err as { detail?: unknown }).detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first && typeof first === "object" && "msg" in first) {
        return String((first as { msg: unknown }).msg)
      }
    }
    if (typeof detail === "string" && detail) return detail
  }
  return "Something went wrong."
}

export const handleError = function (
  this: (msg: string) => void,
  err: unknown,
) {
  const message = extractErrorMessage(err)
  this(message)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

export { ApiError }