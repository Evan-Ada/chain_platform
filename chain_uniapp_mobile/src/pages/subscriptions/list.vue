<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { subscriptionApi } from '@/api/subscription'

defineOptions({ name: 'SubscriptionList' })
definePageConfig({ navigationBarTitleText: '订阅列表' })

const subscriptions = ref<any[]>([])
const loading = ref(false)

async function fetchSubscriptions() {
  loading.value = true
  try {
    const res = await subscriptionApi.listSubscriptions() as any
    subscriptions.value = res?.data?.data ?? res?.data ?? []
  } catch (e) {
    console.error('加载订阅列表失败', e)
  } finally {
    loading.value = false
  }
}

async function onPullDownRefresh() {
  await fetchSubscriptions()
  uni.stopPullDownRefresh()
}

function goDetail(id: string) {
  uni.navigateTo({ url: `/pages/subscriptions/detail?id=${id}` })
}

function getScheduleLabel(type?: string) {
  const map: Record<string, string> = { cron: 'Cron', interval: '间隔', manual: '手动' }
  return map[type ?? ''] ?? type ?? ''
}

onMounted(() => {
  fetchSubscriptions()
})
</script>

<template>
  <view class="min-h-screen bg-gray-50 px-4 py-4">
    <template v-if="loading">
      <view class="flex items-center justify-center py-20">
        <text class="text-gray-400">加载中...</text>
      </view>
    </template>

    <template v-else-if="subscriptions.length === 0">
      <view class="flex flex-col items-center justify-center py-20">
        <text class="text-4xl">📡</text>
        <text class="mt-2 text-sm text-gray-400">暂无订阅</text>
      </view>
    </template>

    <template v-else>
      <view
        v-for="item in subscriptions"
        :key="item.id"
        class="mb-3 rounded-xl bg-white p-4 shadow-sm"
        @click="goDetail(item.id)"
      >
        <view class="flex items-start justify-between">
          <view class="flex-1">
            <text class="text-base font-medium">{{ item.name }}</text>

            <!-- keywords -->
            <view v-if="item.keywords?.length" class="mt-2 flex flex-wrap gap-1">
              <view
                v-for="kw in item.keywords"
                :key="kw"
                class="rounded bg-orange-50 px-2 py-0.5 text-xs text-orange-500"
              >
                {{ kw }}
              </view>
            </view>

            <!-- schedule -->
            <view class="mt-2 flex items-center gap-2 text-xs text-gray-400">
              <text>周期：{{ getScheduleLabel(item.schedule_type) }}</text>
              <text v-if="item.schedule_cron">｜ {{ item.schedule_cron }}</text>
            </view>
          </view>

          <!-- enabled badge -->
          <view
            class="ml-2 shrink-0 rounded px-2 py-0.5 text-xs"
            :class="item.enabled ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'"
          >
            {{ item.enabled ? '已启用' : '已禁用' }}
          </view>
        </view>
      </view>
    </template>
  </view>
</template>
