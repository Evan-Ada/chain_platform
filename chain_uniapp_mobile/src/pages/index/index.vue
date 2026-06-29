<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { pushApi } from '@/api/push'

defineOptions({
  name: 'Home',
})
definePageConfig({
  type: 'home',
  style: {
    navigationStyle: 'custom',
    navigationBarTitleText: '首页',
  },
})

const recentMessages = ref<any[]>([])
const loading = ref(false)

function getImportanceColor(imp?: string) {
  const map: Record<string, string> = { high: '#f56c6c', medium: '#e6a23c', low: '#67c23a' }
  return map[imp ?? ''] ?? '#999'
}

function getImportanceLabel(imp?: string) {
  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return map[imp ?? ''] ?? ''
}

async function fetchRecentMessages() {
  loading.value = true
  try {
    const res = await pushApi.listMessages({ page_size: 3 } as any) as any
    const data = res?.data?.data ?? res?.data ?? []
    recentMessages.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('加载最近消息失败', e)
  } finally {
    loading.value = false
  }
}

async function refreshBadge() {
  try {
    const res = await pushApi.unreadCount() as any
    const count = res?.data?.data?.unread_count ?? res?.data?.unread_count ?? 0
    if (count > 0) {
      uni.setTabBarBadge({ index: 1, text: String(count) })
    } else {
      uni.removeTabBarBadge({ index: 1 })
    }
  } catch {}
}

onMounted(async () => {
  await fetchRecentMessages()
  await refreshBadge()
})
</script>

<template>
  <view class="min-h-screen bg-gray-50 px-4 pt-safe">
    <!-- Logo + 标题 -->
    <view class="mt-10">
      <image src="/static/logo.svg" alt="" class="mx-auto block h-20 w-20" />
    </view>
    <view class="mt-3 text-center text-2xl font-bold text-[#018d71]">
      Chain Platform
    </view>

    <!-- 最近消息卡片 -->
    <view class="mt-6">
      <view class="mb-3 flex items-center justify-between px-1">
        <text class="text-base font-medium">最近消息</text>
        <text
          class="cursor-pointer text-sm text-blue-500"
          @click="uni.switchTab({ url: '/pages/messages/messages' })"
        >
          查看全部 →
        </text>
      </view>

      <template v-if="loading">
        <view class="rounded-xl bg-white p-6 text-center text-sm text-gray-400">
          加载中...
        </view>
      </template>

      <template v-else-if="recentMessages.length === 0">
        <view class="rounded-xl bg-white py-8 text-center">
          <text class="text-3xl">📭</text>
          <view class="mt-2 text-sm text-gray-400">暂无消息</view>
        </view>
      </template>

      <template v-else>
        <view
          v-for="item in recentMessages"
          :key="item.id"
          class="mb-3 rounded-xl bg-white p-4 shadow-sm"
          @click="uni.navigateTo({ url: `/pages/messages/detail?id=${item.id}` })"
        >
          <view class="flex items-start justify-between">
            <text class="flex-1 pr-2 text-base font-medium leading-snug">{{ item.title }}</text>
            <view
              v-if="item.importance"
              class="shrink-0 rounded px-2 py-0.5 text-xs text-white"
              :style="{ backgroundColor: getImportanceColor(item.importance) }"
            >
              {{ getImportanceLabel(item.importance) }}
            </view>
          </view>

          <view v-if="item.summary" class="mt-1 text-sm text-gray-500 line-clamp-1">
            {{ item.summary }}
          </view>

          <view class="mt-2 flex items-center justify-between text-xs text-gray-400">
            <text>{{ item.source_name ?? '' }}</text>
            <text>{{ item.push_date ? item.push_date.slice(11, 16) : '' }}</text>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>
