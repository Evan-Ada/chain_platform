<template>
  <view class="detail-page">
    <view class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <text class="page-title">洞见详情</text>
    </view>

    <scroll-view scroll-y class="content-scroll">
      <view v-if="loading" class="loading-text">加载中...</view>
      <view v-else-if="insight" class="insight-detail">
        <!-- 原文 -->
        <view class="section">
          <view class="section-label">原文</view>
          <view class="raw-text">{{ insight.raw_text }}</view>
        </view>

        <!-- 状态 -->
        <view class="status-row">
          <text :class="['status-badge', insight.status]">
            {{ statusText(insight.status) }}
          </text>
          <text v-for="tag in insight.tags" :key="tag" class="tag-badge">{{ tag }}</text>
        </view>

        <!-- AI 解读 -->
        <view v-if="insight.status === 'done' && insight.ai_interpretation" class="section">
          <view class="section-label">AI 解读</view>
          <view class="interpretation">
            <view v-if="insight.ai_interpretation.core_viewpoint" class="interp-item">
              <text class="interp-label">核心观点</text>
              <text class="interp-text">{{ insight.ai_interpretation.core_viewpoint }}</text>
            </view>
            <view v-if="insight.ai_interpretation.emotional_tone" class="interp-item">
              <text class="interp-label">情绪基调</text>
              <text class="interp-text">{{ insight.ai_interpretation.emotional_tone }}</text>
            </view>
            <view v-if="insight.ai_interpretation.motivation" class="interp-item">
              <text class="interp-label">可能的动机</text>
              <text class="interp-text">{{ insight.ai_interpretation.motivation }}</text>
            </view>
            <view v-if="insight.ai_interpretation.actionable_suggestions?.length" class="interp-item">
              <text class="interp-label">可执行建议</text>
              <view v-for="(s, i) in insight.ai_interpretation.actionable_suggestions" :key="i" class="suggestion-item">
                {{ i + 1 }}. {{ s }}
              </view>
            </view>
          </view>
        </view>

        <!-- 失败信息 -->
        <view v-if="insight.status === 'failed' && insight.error_message" class="section error-section">
          <text class="error-text">解读失败：{{ insight.error_message }}</text>
        </view>

        <!-- 追问链 -->
        <view v-if="insight.follow_ups?.length" class="section">
          <view class="section-label">追问</view>
          <view v-for="fu in insight.follow_ups" :key="fu.id" class="followup-item">
            <text class="followup-text">{{ fu.raw_text }}</text>
            <view v-if="fu.ai_interpretation?.core_viewpoint" class="followup-interp">
              → {{ fu.ai_interpretation.core_viewpoint }}
            </view>
          </view>
        </view>

        <!-- 追问输入 -->
        <view class="followup-form">
          <textarea
            v-model="followUpText"
            class="followup-input"
            placeholder="输入你的追问..."
            :maxlength="1000"
          />
          <button class="btn-followup" :disabled="!followUpText.trim() || submitting" @click="handleFollowUp">
            {{ submitting ? '提交中...' : '追问' }}
          </button>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { insightApi, type InsightItem } from '@/api/insight'

const loading = ref(false)
const submitting = ref(false)
const insight = ref<InsightItem | null>(null)
const followUpText = ref('')

let insightId = 0

async function fetchDetail() {
  loading.value = true
  try {
    const res = await insightApi.get(insightId) as any
    insight.value = res?.data?.data ?? res?.data ?? null
  } finally {
    loading.value = false
  }
}

async function handleFollowUp() {
  if (!followUpText.value.trim()) return
  submitting.value = true
  try {
    await insightApi.followUp(insightId, followUpText.value.trim())
    uni.showToast({ title: '追问成功', icon: 'success' })
    followUpText.value = ''
    fetchDetail()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '追问失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBack() {
  uni.navigateBack()
}

function statusText(status: string) {
  return { pending: '解读中', done: '已解读', failed: '失败' }[status] || status
}

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  insightId = Number(currentPage?.options?.id || 0)
  if (insightId) fetchDetail()
})
</script>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f9fafb;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.btn-back {
  background: none;
  border: none;
  font-size: 16px;
  color: #3b82f6;
  padding: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.content-scroll {
  flex: 1;
  padding: 16px;
}

.insight-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.raw-text {
  font-size: 15px;
  line-height: 1.7;
  color: #333;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.status-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
}

.status-badge.pending { background: #fef3c7; color: #d97706; }
.status-badge.done { background: #d1fae5; color: #059669; }
.status-badge.failed { background: #fee2e2; color: #dc2626; }

.tag-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: #e5e7eb;
  color: #666;
}

.interpretation {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.interp-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.interp-label {
  font-size: 12px;
  color: #999;
}

.interp-text {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.suggestion-item {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin-left: 8px;
}

.error-section {
  background: #fee2e2;
}

.error-text {
  color: #dc2626;
  font-size: 14px;
}

.followup-item {
  padding: 10px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 8px;
}

.followup-text {
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.followup-interp {
  margin-top: 6px;
  font-size: 13px;
  color: #666;
}

.followup-form {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.followup-input {
  width: 100%;
  min-height: 80px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 10px;
  font-size: 14px;
  resize: none;
  box-sizing: border-box;
}

.btn-followup {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 10px;
  font-size: 14px;
}

.btn-followup:disabled {
  background: #93c5fd;
}

.loading-text {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>
