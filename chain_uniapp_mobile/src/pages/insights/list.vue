<template>
  <view class="insights-list">
    <!-- 顶部标题 -->
    <view class="page-header">
      <text class="page-title">我的洞见</text>
      <view class="header-actions">
        <button class="btn-add" @click="goAdd">+ 录入</button>
      </view>
    </view>

    <!-- 标签筛选 -->
    <scroll-view scroll-x class="tag-scroll">
      <view class="tag-list">
        <view
          v-for="tag in allTags"
          :key="tag"
          :class="['tag-item', { active: selectedTag === tag }]"
          @click="selectTag(tag)"
        >
          {{ tag }}
        </view>
      </view>
    </scroll-view>

    <!-- 列表 -->
    <scroll-view scroll-y class="content-scroll" @scrolltolower="loadMore">
      <view v-if="loading && insights.length === 0" class="loading-text">加载中...</view>
      <view v-else-if="insights.length === 0" class="empty-text">暂无洞见</view>
      <view v-else class="insight-cards">
        <view
          v-for="item in insights"
          :key="item.id"
          class="insight-card"
          @click="goDetail(item.id)"
        >
          <!-- 原文 -->
          <view class="raw-text">{{ item.raw_text.slice(0, 100) }}{{ item.raw_text.length > 100 ? '...' : '' }}</view>

          <!-- 状态 + 标签 -->
          <view class="card-meta">
            <text :class="['status-badge', item.status]">
              {{ statusText(item.status) }}
            </text>
            <text v-for="tag in item.tags?.slice(0, 3)" :key="tag" class="tag-badge">
              {{ tag }}
            </text>
            <text class="date-text">{{ formatDate(item.created_at) }}</text>
          </view>

          <!-- AI 解读预览 -->
          <view v-if="item.status === 'done' && item.ai_interpretation?.core_viewpoint" class="interpretation-preview">
            <text class="interpretation-label">核心观点：</text>
            <text class="interpretation-text">{{ item.ai_interpretation.core_viewpoint }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { insightApi, type InsightItem } from '@/api/insight'

const insights = ref<InsightItem[]>([])
const loading = ref(false)
const selectedTag = ref<string | null>(null)
const allTags = ref<string[]>([])

async function fetchList() {
  loading.value = true
  try {
    const res = await insightApi.list({ tag: selectedTag.value || undefined }) as any
    const data = res?.data?.data ?? res?.data ?? {}
    insights.value = data.res ?? []
    // 收集所有标签
    const tagSet = new Set<string>()
    insights.value.forEach((i: InsightItem) => i.tags?.forEach((t: string) => tagSet.add(t)))
    allTags.value = Array.from(tagSet)
  } finally {
    loading.value = false
  }
}

function selectTag(tag: string | null) {
  selectedTag.value = selectedTag.value === tag ? null : tag
  fetchList()
}

function goAdd() {
  uni.navigateTo({ url: '/pages/insights/add' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/insights/detail?id=${id}` })
}

function loadMore() {
  // TODO: 分页加载
}

function statusText(status: string) {
  return { pending: '解读中', done: '已解读', failed: '失败' }[status] || status
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return dateStr.slice(0, 10)
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.insights-list {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.btn-add {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 14px;
}

.tag-scroll {
  background: #fff;
  padding: 8px 16px;
  white-space: nowrap;
}

.tag-list {
  display: flex;
  gap: 8px;
}

.tag-item {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  background: #f0f0f0;
  color: #666;
}

.tag-item.active {
  background: #3b82f6;
  color: #fff;
}

.content-scroll {
  flex: 1;
  padding: 12px 16px;
}

.insight-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.raw-text {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.status-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.status-badge.pending { background: #fef3c7; color: #d97706; }
.status-badge.done { background: #d1fae5; color: #059669; }
.status-badge.failed { background: #fee2e2; color: #dc2626; }

.tag-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #e5e7eb;
  color: #666;
}

.date-text {
  font-size: 11px;
  color: #999;
  margin-left: auto;
}

.interpretation-preview {
  font-size: 12px;
  color: #666;
  background: #f9fafb;
  padding: 8px;
  border-radius: 4px;
}

.interpretation-label {
  font-weight: 500;
  color: #333;
}

.loading-text,
.empty-text {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}
</style>
