<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { pushApi } from '@/api/push'

defineOptions({ name: 'PushTime' })
definePageConfig({ navigationBarTitleText: '推送设置' })

const pushTime = ref('09:00')
const dailyDigest = ref(false)
const importanceFilter = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)

const importanceOptions = [
  { label: '高', value: 'high' },
  { label: '中', value: 'medium' },
  { label: '低', value: 'low' },
]

async function fetchPreference() {
  loading.value = true
  try {
    const res = await pushApi.getPreference() as any
    const pref = res?.data?.data ?? res?.data ?? {}
    pushTime.value = pref.push_time ?? '09:00'
    dailyDigest.value = pref.daily_digest ?? false
    importanceFilter.value = pref.importance_filter ?? []
  } catch (e) {
    console.error('加载推送偏好失败', e)
  } finally {
    loading.value = false
  }
}

async function savePreference() {
  saving.value = true
  try {
    await pushApi.updatePreference({
      push_time: pushTime.value,
      daily_digest: dailyDigest.value,
      importance_filter: importanceFilter.value,
    } as any)
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'error' })
  } finally {
    saving.value = false
  }
}

function onTimeChange(e: any) {
  pushTime.value = e.detail.value
}

function toggleImportance(val: string) {
  const idx = importanceFilter.value.indexOf(val)
  if (idx >= 0) {
    importanceFilter.value.splice(idx, 1)
  } else {
    importanceFilter.value.push(val)
  }
}

onMounted(() => {
  fetchPreference()
})
</script>

<template>
  <view class="min-h-screen bg-gray-50 px-4 py-4">
    <template v-if="loading">
      <view class="flex items-center justify-center py-20">
        <text class="text-gray-400">加载中...</text>
      </view>
    </template>

    <template v-else>
      <view class="rounded-xl bg-white p-4 shadow-sm">
        <!-- 推送时间 -->
        <view class="py-3">
          <view class="mb-2 text-sm text-gray-600">每日推送时间</view>
          <picker mode="time" :value="pushTime" @change="onTimeChange">
            <view class="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
              <text class="text-base">{{ pushTime }}</text>
              <text class="text-gray-400">点击选择</text>
            </view>
          </picker>
        </view>

        <view class="my-3 h-px bg-gray-100" />

        <!-- 每日摘要 -->
        <view class="flex items-center justify-between py-3">
          <view class="text-sm text-gray-600">每日摘要</view>
          <switch :checked="dailyDigest" @change="(e: any) => { dailyDigest = e.detail.value }" />
        </view>

        <view class="my-3 h-px bg-gray-100" />

        <!-- 重要性筛选 -->
        <view class="py-3">
          <view class="mb-2 text-sm text-gray-600">重要性筛选</view>
          <view class="flex gap-2">
            <view
              v-for="opt in importanceOptions"
              :key="opt.value"
              class="cursor-pointer rounded-full px-4 py-2 text-sm"
              :class="importanceFilter.includes(opt.value)
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600'"
              @click="toggleImportance(opt.value)"
            >
              {{ opt.label }}
            </view>
          </view>
        </view>
      </view>

      <!-- 保存按钮 -->
      <view class="mt-6">
        <button
          class="w-full rounded-lg bg-green-500 py-3 text-sm text-white"
          :disabled="saving"
          @click="savePreference"
        >
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </view>
    </template>
  </view>
</template>
