<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { subscriptionApi } from '@/api/subscription'
import dayjs from 'dayjs'

defineOptions({ name: 'SubscriptionDetail' })
definePageConfig({ navigationBarTitleText: '订阅详情' })

const id = ref('')
const subscription = ref<any>(null)
const contents = ref<any[]>([])
const loading = ref(true)
const running = ref(false)

async function fetchData() {
  loading.value = true
  try {
    // 获取订阅详情
    const res = await subscriptionApi.listSubscriptions() as any
    const list: any[] = res?.data?.data ?? res?.data ?? []
    subscription.value = list.find((s: any) => s.id === id.value) ?? null

    // 获取该订阅的内容
    const contentRes = await subscriptionApi.listContents(
      { subscription_id: id.value, page_size: 50 } as any,
    ) as any
    contents.value = contentRes?.data?.data ?? contentRes?.data ?? []
  } catch (e) {
    console.error('加载订阅详情失败', e)
  } finally {
    loading.value = false
  }
}

async function handleRunNow() {
  if (running.value) return
  running.value = true
  try {
    await subscriptionApi.runNow(id.value)
    uni.showToast({ title: '已触发抓取', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '触发失败', icon: 'error' })
  } finally {
    running.value = false
  }
}

function getImportanceColor(imp?: string) {
  const map: Record<string, string> = { high: '#f56c6c', medium: '#e6a23c', low: '#67c23a' }
  return map[imp ?? ''] ?? '#999'
}

onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  id.value = currentPage?.options?.id ?? ''
  await fetchData()
})
</script>

<template>
  <view class="min-h-screen bg-gray-50 px-4 py-4">
    <template v-if="loading">
      <view class="flex items-center justify-center py-20">
        <text class="text-gray-400">加载中...</text>
      </view>
    </template>

    <template v-else-if="!subscription">
      <view class="flex flex-col items-center justify-center py-20">
        <text class="text-gray-400">订阅不存在</text>
      </view>
    </template>

    <template v-else>
      <!-- 订阅信息卡片 -->
      <view class="rounded-xl bg-white p-4 shadow-sm">
        <view class="text-lg font-bold">{{ subscription.name }}</view>

        <!-- keywords -->
        <view v-if="subscription.keywords?.length" class="mt-3 flex flex-wrap gap-1">
          <view
            v-for="kw in subscription.keywords"
            :key="kw"
            class="rounded bg-orange-50 px-2 py-0.5 text-xs text-orange-500"
          >
            {{ kw }}
          </view>
        </view>

        <!-- sources -->
        <view v-if="subscription.sources?.length" class="mt-3">
          <text class="text-sm text-gray-500">来源：</text>
          <text class="text-sm">{{ subscription.sources.join('、') }}</text>
        </view>

        <!-- cron -->
        <view v-if="subscription.schedule_cron" class="mt-2 text-sm text-gray-500">
          Cron：{{ subscription.schedule_cron }}
        </view>

        <!-- 状态 -->
        <view class="mt-3">
          <view
            class="inline-block rounded px-2 py-0.5 text-xs"
            :class="subscription.enabled ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'"
          >
            {{ subscription.enabled ? '已启用' : '已禁用' }}
          </view>
        </view>
      </view>

      <!-- 立即抓取按钮 -->
      <view class="mt-4">
        <button
          class="w-full rounded-lg bg-blue-500 py-3 text-sm text-white"
          :disabled="running"
          @click="handleRunNow"
        >
          {{ running ? '抓取中...' : '立即抓取' }}
        </button>
      </view>

      <!-- 内容列表 -->
      <view class="mt-6">
        <view class="mb-2 text-base font-medium">最近内容</view>

        <template v-if="contents.length === 0">
          <view class="rounded-xl bg-white py-10 text-center text-sm text-gray-400">
            暂无内容
          </view>
        </template>

        <view
          v-for="item in contents"
          :key="item.id"
          class="mb-3 rounded-xl bg-white p-4 shadow-sm"
        >
          <view class="flex items-start justify-between">
            <text class="flex-1 text-base font-medium leading-snug">{{ item.title }}</text>
            <view
              v-if="item.importance"
              class="ml-2 shrink-0 rounded px-2 py-0.5 text-xs text-white"
              :style="{ backgroundColor: getImportanceColor(item.importance) }"
            >
              {{ item.importance }}
            </view>
          </view>

          <view v-if="item.summary" class="mt-1 text-sm text-gray-500 line-clamp-2">
            {{ item.summary }}
          </view>

          <view v-if="item.push_date" class="mt-2 text-xs text-gray-400">
            {{ dayjs(item.push_date).format('YYYY-MM-DD HH:mm') }}
          </view>
        </view>
      </view>
    </template>
  </view>
</template>
