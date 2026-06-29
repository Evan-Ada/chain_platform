<template>
  <view class="add-page">
    <view class="page-header">
      <text class="page-title">录入洞见</text>
    </view>

    <view class="form-content">
      <view class="form-item">
        <textarea
          v-model="rawText"
          class="text-input"
          placeholder="写下你的想法、灵感、反思..."
          :maxlength="2000"
        />
        <text class="char-count">{{ rawText.length }}/2000</text>
      </view>
    </view>

    <view class="form-actions">
      <button class="btn-cancel" @click="goBack">取消</button>
      <button class="btn-submit" :disabled="!rawText.trim() || submitting" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { insightApi } from '@/api/insight'

const rawText = ref('')
const submitting = ref(false)

async function handleSubmit() {
  if (!rawText.value.trim()) return
  submitting.value = true
  try {
    await insightApi.add(rawText.value.trim())
    uni.showToast({ title: '提交成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.add-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
}

.page-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.form-content {
  flex: 1;
  padding: 16px;
}

.form-item {
  position: relative;
}

.text-input {
  width: 100%;
  min-height: 200px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
  box-sizing: border-box;
}

.char-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: #999;
}

.form-actions {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel,
.btn-submit {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 15px;
  border: none;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-submit {
  background: #3b82f6;
  color: #fff;
}

.btn-submit:disabled {
  background: #93c5fd;
}
</style>
