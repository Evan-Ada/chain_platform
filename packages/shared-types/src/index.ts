/**
 * 跨端共享的本地 types（与 OpenAPI 无关）。
 * 例如：localStorage key、事件名、本地配置 schema。
 * OpenAPI 生成的 types 见 @chain/api-client。
 */

export const StorageKeys = {
  ACCESS_TOKEN: "chain:access_token",
  USER_PROFILE: "chain:user_profile",
  LOCALE: "chain:locale",
} as const;

export const EventNames = {
  AUTH_TOKEN_EXPIRED: "chain:auth-token-expired",
  USER_LOGGED_OUT: "chain:user-logged-out",
} as const;
