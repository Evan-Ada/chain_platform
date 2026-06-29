/**
 * Chain 业务错误码常量。
 * 与 chain_fastapi_server/app/core/errors.py 手工对齐维护。
 * 编号规则：B 表示业务（Business），后接 4 位数字。
 */
export const ErrorCodes = {
  UNKNOWN: "B0000",
  UNAUTHORIZED: "B1001",
  FORBIDDEN: "B1002",
  NOT_FOUND: "B1003",
  VALIDATION_FAILED: "B1004",
  RATE_LIMITED: "B1005",
  CONFLICT: "B1006",
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];

export const ErrorMessages: Record<ErrorCode, string> = {
  [ErrorCodes.UNKNOWN]: "未知错误",
  [ErrorCodes.UNAUTHORIZED]: "未登录或登录已过期",
  [ErrorCodes.FORBIDDEN]: "无权限访问",
  [ErrorCodes.NOT_FOUND]: "资源不存在",
  [ErrorCodes.VALIDATION_FAILED]: "请求参数校验失败",
  [ErrorCodes.RATE_LIMITED]: "请求过于频繁",
  [ErrorCodes.CONFLICT]: "资源状态冲突",
};
