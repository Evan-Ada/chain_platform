<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { pushApi } from '@/api/push'
import dayjs from 'dayjs'

defineOptions({ name: 'Messages' })
definePageConfig({ navigationBarTitleText: '消息中心' })

// 状态
const messages = ref<any[]>([])
const loading = ref(false)
const selectedImportance = ref<string[]>([])
const pageNum = ref(1)
const pageSize = ref(20)
const hasMore = ref(true)

// importance 选项
const importanceOptions = [
  { label: '高', value: 'high', color: 'red' },
  { label: '中', value: 'medium', color: 'orange' },
  { label: '低', value: 'low', color: 'green' },
]

// 格式化时间分组
function formatGroup(dateStr: string) {
  const date = dayjs(dateStr)
  const today = dayjs().startOf('day')
  const yesterday = dayjs().subtract(1, 'day').startOf('day')

  if (date.isSame(today, 'day')) return '今天'
  if (date.isSame(yesterday, 'day')) return '昨天'
  return '更早'
}

// 按日期分组
function groupByDate(list: any[]) {
  const groups: Record<string, any[]> = {}
  for (const item of list) {
    const key = formatGroup(item.push_date)
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
  }
  return groups
}

// 加载消息
async function fetchMessages(reset = false) {
  if (loading.value) return
  if (!reset && !hasMore.value) return

  loading.value = true
  try {
    if (reset) {
      pageNum.value = 1
      hasMore.value = true
    }

    const res = await pushApi.listMessages({
      page_num: pageNum.value,
      page_size: pageSize.value,
      importance: selectedImportance.value.length > 0 ? selectedImportance.value.join(',') : undefined,
    } as any)

    const data = (res as any)?.data?.data ?? res?.data ?? []
    if (reset) {
      messages.value = data
    } else {
      messages.value.push(...data)
    }
    hasMore.value = data.length >= pageSize.value
    pageNum.value++
  } catch (e) {
    console.error('加载消息失败', e)
  } finally {
    loading.value = false
  }
}

// 下拉刷新
async function onPullDownRefresh() {
  await fetchMessages(true)
  await refreshBadge()
  uni.stopPullDownRefresh()
}

// 上拉加载
async function onReachBottom() {
  if (hasMore.value) await fetchMessages(false)
}

// 刷新 tabbar badge
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

// 切换 importance 筛选
async function toggleImportance(val: string) {
  const idx = selectedImportance.value.indexOf(val)
  if (idx >= 0) {
    selectedImportance.value.splice(idx, 1)
  } else {
    selectedImportance.value.push(val)
  }
  await fetchMessages(true)
}

// 查看详情
function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/messages/detail?id=${id}` })
}

// 获取 importance 颜色
function getImportanceColor(imp?: string) {
  const map: Record<string, string> = { high: '#f56c6c', medium: '#e6a23c', low: '#67c23a' }
  return map[imp ?? ''] ?? '#999'
}

onMounted(async () => {
  await fetchMessages(true)
})
</script>

<template>
  <view class="min-h-screen bg-gray-50">
    <!-- 顶部 importance 筛选 -->
    <view class="sticky top-0 z-10 bg-white px-4 py-3">
      <view class="flex items-center gap-2">
        <text class="text-sm text-gray-500">筛选：</text>
        <view
          v-for="opt in importanceOptions"
          :key="opt.value"
          class="chip cursor-pointer rounded-full px-3 py-1 text-xs"
          :class="selectedImportance.includes(opt.value)
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-600'"
          @click="toggleImportance(opt.value)"
        >
          {{ opt.label }}
        </view>
      </view>
    </view>

    <!-- 消息列表 -->
    <view class="px-4 py-2">
      <template v-if="messages.length === 0 && !loading">
        <view class="flex flex-col items-center justify-center py-20 text-gray-400">
          <text class="text-4xl">📭</text>
          <text class="mt-2 text-sm">暂无消息</text>
        </view>
      </template>

      <template v-else>
        <!-- 按日期分组 -->
        <view v-for="(items, group) in groupByDate(messages)" :key="group">
          <view class="sticky top-13 z-5 bg-gray-50 px-2 py-1">
            <text class="text-xs text-gray-400">{{ group }}</text>
          </view>

          <view
            v-for="item in items"
            :key="item.id"
            class="mb-3 rounded-xl bg-white p-4 shadow-sm"
            @click="goDetail(item.id)"
          >
            <!-- title + importance badge -->
            <view class="flex items-start justify-between">
              <text class="flex-1 text-base font-medium leading-snug">{{ item.title }}</text>
              <view
                class="ml-2 shrink-0 rounded px-2 py-0.5 text-xs text-white"
                :style="{ backgroundColor: getImportanceColor(item.importance) }"
              >
                {{ importanceOptions.find(o => o.value === item.importance)?.label ?? item.importance }}
              </view>
            </view>

            <!-- summary -->
            <text v-if="item.summary" class="mt-1 block text-sm text-gray-500 line-clamp-2">
              {{ item.summary }}
            </text>

            <!-- tags + 时间 -->
            <view class="mt-2 flex flex-wrap items-center gap-1">
              <view
                v-for="tag in (item.tags ?? [])"
                :key="tag"
                class="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-500"
              >
                {{ tag }}
              </view>
              <text class="ml-auto text-xs text-gray-400">
                {{ item.push_date ? dayjs(item.push_date).format('HH:mm') : '' }}
              </text>
            </view>
          </view>
        </view>
      </template>

      <!-- 加载更多 -->
      <view v-if="loading" class="py-4 text-center text-sm text-gray-400">
        <text>加载中...</text>
      </view>
      <view v-else-if="!hasMore && messages.length > 0" class="py-4 text-center text-sm text-gray-400">
        <text>没有更多了</text>
      </view>
    </view>
  </view>
</template>
