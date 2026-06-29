/**
 * 订阅相关 API
 */
import type {
  SubscriptionListSubscriptionsData,
  SubscriptionListContentsData,
  SubscriptionRunNowData,
  SearchContentsM,
  RunNowM,
} from '@chain/api-client/types.gen'
import {
  subscriptionListSubscriptions,
  subscriptionListContents,
  subscriptionRunNow,
} from '@chain/api-client'

/**
 * 查询当前用户的订阅列表
 */
export function listSubscriptions(options?: { client?: any }) {
  return subscriptionListSubscriptions({ client: options?.client })
}

/**
 * 查询订阅的内容列表
 * @param data 包含 subscription_id 等筛选条件
 */
export function listContents(data: SearchContentsM, options?: { client?: any }) {
  return subscriptionListContents({ body: data, client: options?.client })
}

/**
 * 立即触发订阅抓取
 * @param id 订阅 ID
 */
export function runNow(id: string, options?: { client?: any }) {
  return subscriptionRunNow({ body: { id } as RunNowM, client: options?.client })
}

export const subscriptionApi = {
  listSubscriptions,
  listContents,
  runNow,
}
