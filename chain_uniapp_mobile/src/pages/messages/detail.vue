<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { pushApi } from '@/api/push'
import dayjs from 'dayjs'

defineOptions({ name: 'MessageDetail' })
definePageConfig({ navigationBarTitleText: '消息详情' })

const id = ref('')
const detail = ref<any>(null)
const loading = ref(true)

function getImportanceColor(imp?: string) {
  const map: Record<string, string> = { high: '#f56c6c', medium: '#e6a23c', low: '#67c23a' }
  return map[imp ?? ''] ?? '#999'
}

function getImportanceLabel(imp?: string) {
  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return map[imp ?? ''] ?? imp ?? ''
}

async function fetchDetail() {
  loading.value = true
  try {
    const res = await pushApi.listMessages({ page_size: 100 } as any) as any
    const list: any[] = res?.data?.data ?? res?.data ?? []
    detail.value = list.find((m: any) => m.id === id.value) ?? null
  } catch (e) {
    console.error('加载详情失败', e)
  } finally {
    loading.value = false
  }
}

async function markAllRead() {
  if (!detail.value) return
  try {
    await pushApi.markAsRead([detail.value.id])
    uni.showToast({ title: '已标记已读', icon: 'success' })
    detail.value.is_read = true
    // 刷新 badge
    try {
      const res = await pushApi.unreadCount() as any
      const count = res?.data?.data?.unread_count ?? res?.data?.unread_count ?? 0
      if (count > 0) {
        uni.setTabBarBadge({ index: 1, text: String(count) })
      } else {
        uni.removeTabBarBadge({ index: 1 })
      }
    } catch {}
  } catch (e) {
    uni.showToast({ title: '操作失败', icon: 'error' })
  }
}

function openUrl(url?: string) {
  if (!url) return
  // #ifdef H5
  window.open(url)
  // #endif
  // #ifndef H5
  uni.navigateTo({
    url: `/pages/webview/webview?url=${encodeURIComponent(url)}`,
  })
  // #endif
}

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  id.value = currentPage?.options?.id ?? ''
  await fetchDetail()
})
</script>

<template>
  <view class="min-h-screen bg-gray-50 px-4 py-4">
    <template v-if="loading">
      <view class="flex items-center justify-center py-20">
        <text class="text-gray-400">加载中...</text>
      </view>
    </template>

    <template v-else-if="!detail">
      <view class="flex flex-col items-center justify-center py-20">
        <text class="text-gray-400">消息不存在</text>
      </view>
    </template>

    <template v-else>
      <!-- 卡片 -->
      <view class="rounded-xl bg-white p-4 shadow-sm">
        <!-- 标题 -->
        <view class="flex items-start justify-between">
          <text class="flex-1 text-lg font-bold leading-relaxed">{{ detail.title }}</text>
          <view
            class="ml-2 shrink-0 rounded px-2 py-0.5 text-xs text-white"
            :style="{ backgroundColor: getImportanceColor(detail.importance) }"
          >
            {{ getImportanceLabel(detail.importance) }}
          </view>
        </view>

        <!-- 元信息 -->
        <view class="mt-3 flex flex-wrap gap-3 text-sm text-gray-500">
          <text v-if="detail.source_name">来源：{{ detail.source_name }}</text>
          <text v-if="detail.push_date">
            {{ dayjs(detail.push_date).format('YYYY-MM-DD HH:mm') }}
          </text>
        </view>

        <!-- 标签 -->
        <view v-if="detail.tags?.length" class="mt-3 flex flex-wrap gap-1">
          <view
            v-for="tag in detail.tags"
            :key="tag"
            class="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-500"
          >
            {{ tag }}
          </view>
        </view>

        <!-- 摘要 -->
        <view v-if="detail.summary" class="mt-4 text-sm text-gray-600 leading-relaxed">
          {{ detail.summary }}
        </view>

        <!-- 原文链接 -->
        <view v-if="detail.url" class="mt-4">
          <button
            class="rounded-lg bg-blue-500 px-4 py-2 text-sm text-white"
            @click="openUrl(detail.url)"
          >
            打开原文链接
          </button>
        </view>
      </view>

      <!-- 全部已读按钮 -->
      <view class="mt-4">
        <button
          class="w-full rounded-lg bg-green-500 py-3 text-sm text-white"
          @click="markAllRead"
        >
          标记已读
        </button>
      </view>
    </template>
  </view>
</template>
