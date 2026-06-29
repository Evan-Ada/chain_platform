<script setup lang="ts">
import { onHide, onLaunch, onShow } from '@dcloudio/uni-app'
import { navigateToInterceptor } from '@/router/interceptor'

onLaunch(async (options) => {
  console.log('App.vue onLaunch', options)
  // 启动时拉取未读数
  try {
    const { pushApi } = await import('@/api/push')
    const res = await pushApi.unreadCount() as any
    const count = res?.data?.data?.unread_count ?? res?.data?.unread_count ?? 0
    if (count > 0) {
      uni.setTabBarBadge({ index: 1, text: String(count) })
    } else {
      uni.removeTabBarBadge({ index: 1 })
    }
  } catch {}
})
onShow(async (options) => {
  console.log('App.vue onShow', options)
  // 处理直接进入页面路由的情况：如h5直接输入路由、微信小程序分享后进入等
  // https://github.com/feige996/unibest/issues/192
  if (options?.path) {
    navigateToInterceptor.invoke({
      url: `/${options.path}`,
      query: options.query,
    })
  }
  else {
    navigateToInterceptor.invoke({ url: '/' })
  }
  // 前台切换时刷新未读数
  try {
    const { pushApi } = await import('@/api/push')
    const res = await pushApi.unreadCount() as any
    const count = res?.data?.data?.unread_count ?? res?.data?.unread_count ?? 0
    if (count > 0) {
      uni.setTabBarBadge({ index: 1, text: String(count) })
    } else {
      uni.removeTabBarBadge({ index: 1 })
    }
  } catch {}
})
onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss"></style>
