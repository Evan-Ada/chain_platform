<script lang="ts" setup>
import { getHealthStatus } from '@/api/health'

definePage({
  style: {
    'mp-alipay': {
      defaultTitle: '我的',
      // transparentTitle: 'always', // 可选值    auto/always/none
      // titlePenetrate: 'YES',
      titleBarColor: '#ffffff',
    },
  },
})

const apiVersionText = ref('API 版本获取中')

onLoad(async () => {
  try {
    const health = await getHealthStatus()
    apiVersionText.value = `API v${health.version}`
  }
  catch {
    apiVersionText.value = 'API 版本不可用'
  }
})
</script>

<template>
  <view class="flex min-h-screen flex-col bg-white px-4 pb-safe">
    <view class="mt-10 text-center text-green-500">
      我的页面
    </view>
    <view class="mt-auto pb-6 text-center text-gray-400 text-xs">
      {{ apiVersionText }}
    </view>
  </view>
</template>
