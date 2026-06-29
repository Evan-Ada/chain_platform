<script lang="ts" setup>
import { ref } from 'vue'
import { post, get } from '@/utils/api-client-config'
import { useUserStore } from '@/store/user'

defineOptions({
  name: 'Login',
})

definePage({
  style: {
    navigationBarTitleText: '登录',
    navigationStyle: 'custom',
  },
})

const userStore = useUserStore()

const formData = ref({
  username: '',
  password: '',
})

const loading = ref(false)

const handleLogin = async () => {
  if (!formData.value.username) {
    uni.showToast({
      title: '请输入用户名',
      icon: 'none',
    })
    return
  }

  if (!formData.value.password) {
    uni.showToast({
      title: '请输入密码',
      icon: 'none',
    })
    return
  }

  loading.value = true

  try {
    // 调用登录 API (OAuth2 表单格式)
    const result = await post<any>('/api/v1/login/access-token', `username=${encodeURIComponent(formData.value.username)}&password=${encodeURIComponent(formData.value.password)}`,)

    // 更新 Content-Type 为表单格式
    if (result.data && result.data.access_token) {
      // 保存 token
      uni.setStorageSync('token', result.data.access_token)

      // 获取用户信息
      try {
        const userResult = await get<any>('/api/v1/users/me')
        if (userResult.data) {
          // 保存用户信息到 store
          userStore.setUserInfo({
            userId: userResult.data.id || 0,
            username: userResult.data.username || '',
            nickname: userResult.data.full_name || userResult.data.username || '',
            avatar: userResult.data.avatar || '/static/images/default-avatar.png',
          })
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }

      uni.showToast({
        title: '登录成功',
        icon: 'success',
      })

      // 跳转到首页
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/index/index',
        })
      }, 1000)
    } else {
      throw new Error(result.data?.detail || '登录失败')
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    uni.showToast({
      title: error.message || '登录失败，请检查用户名和密码',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

const goToSignup = () => {
  uni.showToast({
    title: '注册功能开发中',
    icon: 'none',
  })
}
</script>

<template>
  <view class="login-container bg-white min-h-screen px-6 pt-safe">
    <!-- Logo -->
    <view class="pt-20 text-center">
      <image src="/static/logo.svg" alt="" class="mx-auto block h-24 w-24" />
      <view class="mt-4 text-3xl font-bold text-gray-800">
        Chain App
      </view>
      <view class="mt-2 text-sm text-gray-500">
        企业级移动应用平台
      </view>
    </view>

    <!-- 登录表单 -->
    <view class="mt-12">
      <view class="mb-6">
        <view class="mb-2 text-sm text-gray-600">
          用户名
        </view>
        <input
          v-model="formData.username"
          type="text"
          placeholder="请输入用户名"
          class="w-full rounded-lg border border-gray-300 px-4 py-3 text-base"
        />
      </view>

      <view class="mb-8">
        <view class="mb-2 text-sm text-gray-600">
          密码
        </view>
        <input
          v-model="formData.password"
          type="password"
          placeholder="请输入密码"
          class="w-full rounded-lg border border-gray-300 px-4 py-3 text-base"
        />
      </view>

      <button
        :disabled="loading"
        class="w-full rounded-lg bg-blue-500 py-3 text-base font-medium text-white"
        :class="{ 'opacity-50': loading }"
        @click="handleLogin"
      >
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <view class="mt-6 text-center text-sm">
        <text class="text-gray-500">
          还没有账号？
        </text>
        <text class="ml-1 text-blue-500" @click="goToSignup">
          立即注册
        </text>
      </view>
    </view>

    <!-- 其他登录方式 -->
    <view class="mt-12">
      <view class="mb-4 text-center text-xs text-gray-400">
        其他登录方式
      </view>
      <view class="flex justify-center gap-8">
        <view class="flex flex-col items-center">
          <view class="flex h-12 w-12 items-center justify-center rounded-full bg-green-500">
            <text class="text-2xl text-white">
              微
            </text>
          </view>
          <text class="mt-2 text-xs text-gray-500">
            微信登录
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.login-container {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}
</style>
