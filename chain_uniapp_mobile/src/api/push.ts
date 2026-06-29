/**
 * 推送消息相关 API
 * 使用共享包 @chain/api-client 封装，底层走 uni.request + Bearer Token 拦截器
 */
import type {
  PushGetPreferenceData,
  PushUpdatePreferenceData,
  PushListMessagesData,
  PushMarkAsReadData,
  PushUnreadCountData,
  UpdatePreferenceM,
  ListMessagesM,
  MarkAsReadM,
} from '@chain/api-client/types.gen'
import {
  pushGetPreference,
  pushUpdatePreference,
  pushListMessages,
  pushMarkAsRead,
  pushUnreadCount,
} from '@chain/api-client'

/**
 * 获取推送偏好设置
 */
export function getPreference(options?: { client?: any }) {
  return pushGetPreference({ client: options?.client })
}

/**
 * 更新推送偏好设置
 */
export function updatePreference(data: UpdatePreferenceM, options?: { client?: any }) {
  return pushUpdatePreference({ body: data, client: options?.client })
}

/**
 * 分页查询推送消息列表
 */
export function listMessages(data: ListMessagesM, options?: { client?: any }) {
  return pushListMessages({ body: data, client: options?.client })
}

/**
 * 批量标记消息为已读
 * @param idList 消息 ID 数组
 */
export function markAsRead(idList: string[], options?: { client?: any }) {
  return pushMarkAsRead({ body: { id_list: idList } as MarkAsReadM, client: options?.client })
}

/**
 * 获取未读消息数量
 */
export function unreadCount(options?: { client?: any }) {
  return pushUnreadCount({ client: options?.client })
}

export const pushApi = {
  getPreference,
  updatePreference,
  listMessages,
  markAsRead,
  unreadCount,
}
