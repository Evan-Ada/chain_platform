/**
 * 标签相关 API
 */
import type { TagListTagsData, ListTagM } from '@chain/api-client/types.gen'
import { tagListTags } from '@chain/api-client'

/**
 * 分页查询标签列表（消息列表按标签筛选用）
 * @param data 筛选条件
 */
export function listTags(data: ListTagM, options?: { client?: any }) {
  return tagListTags({ body: data, client: options?.client })
}

export const tagApi = {
  listTags,
}
