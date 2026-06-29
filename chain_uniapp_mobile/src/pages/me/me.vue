<script lang="ts" setup>
import { getHealthStatus } from '@/api/health'
import { useUserStore } from '@/store/user'

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

const userStore = useUserStore()
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

// 退出登录
const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗?',
    success: (res) => {
      if (res.confirm) {
        // 清除 token
        uni.removeStorageSync('token')
        // 清除用户信息
        userStore.clearUserInfo()

        uni.showToast({
          title: '已退出登录',
          icon: 'success',
        })

        // 跳转到登录页面
        setTimeout(() => {
          uni.redirectTo({
            url: '/pages/login/login',
          })
        }, 1000)
      }
    },
  })
}
</script>

<template>
  <view class="flex min-h-screen flex-col bg-white px-4 pb-safe">
    <!-- 用户信息卡片 -->
    <view class="mt-10 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 p-6 text-white">
      <view class="flex items-center">
        <image
          :src="userStore.userInfo.avatar"
          class="h-16 w-16 rounded-full"
          mode="aspectFill"
        />
        <view class="ml-4 flex-1">
          <view class="text-xl font-bold">
            {{ userStore.userInfo.nickname || userStore.userInfo.username || '未登录' }}
          </view>
          <view class="mt-1 text-sm opacity-80">
            {{ userStore.userInfo.username ? `用户名: ${userStore.userInfo.username}` : '请先登录' }}
          </view>
        </view>
      </view>
    </view>

    <!-- 功能列表 -->
    <view class="mt-6">
      <view class="mb-2 px-4 text-sm text-gray-500">
        账户设置
      </view>
      <view class="rounded-lg bg-gray-50">
        <view
          class="flex items-center justify-between border-b border-gray-100 px-4 py-3"
          @click="uni.showToast({ title: '个人资料功能开发中', icon: 'none' })"
        >
          <view class="flex items-center">
            <text class="text-lg">
              👤
            </text>
            <text class="ml-3">个人资料</text>
          </view>
          <text class="text-gray-400">
            ›
          </text>
        </view>

        <view
          class="flex items-center justify-between border-b border-gray-100 px-4 py-3"
          @click="uni.showToast({ title: '修改密码功能开发中', icon: 'none' })"
        >
          <view class="flex items-center">
            <text class="text-lg">
              🔐
            </text>
            <text class="ml-3">修改密码</text>
          </view>
          <text class="text-gray-400">
            ›
          </text>
        </view>

        <view
          class="flex items-center justify-between px-4 py-3"
          @click="uni.showToast({ title: '设置功能开发中', icon: 'none' })"
        >
          <view class="flex items-center">
            <text class="text-lg">
              ⚙️
            </text>
            <text class="ml-3">设置</text>
          </view>
          <text class="text-gray-400">
            ›
          </text>
        </view>
      </view>
    </view>

    <!-- 退出登录按钮 -->
    <view class="mt-6">
      <button
        class="w-full rounded-lg bg-red-500 py-3 text-base font-medium text-white"
        @click="handleLogout"
      >
        退出登录
      </button>
    </view>

    <!-- 底部信息 -->
    <view class="mt-auto pb-6 text-center text-xs text-gray-400">
      {{ apiVersionText }}
    </view>
  </view>
</template>
