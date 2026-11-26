<script setup lang="ts">
import { useSortingStore } from '../stores/sortingStore'
import { ElButton } from 'element-plus'

const store = useSortingStore()

function handleStart() {
  store.start()
}

function handlePause() {
  store.pause()
}

function handleStop() {
  store.stop()
}

function handleReset() {
  store.reset()
}
</script>

<template>
  <div class="control-panel">
    <h3 class="panel-title">系统控制</h3>

    <div class="control-buttons">
      <ElButton
        type="primary"
        size="large"
        :icon="'VideoPlay'"
        :disabled="store.animationState === 'running'"
        @click="handleStart"
        class="control-btn start-btn"
      >
        开始
      </ElButton>

      <ElButton
        type="warning"
        size="large"
        :icon="'VideoPause'"
        :disabled="store.animationState !== 'running'"
        @click="handlePause"
        class="control-btn pause-btn"
      >
        暂停
      </ElButton>

      <ElButton
        type="danger"
        size="large"
        :icon="'VideoClose'"
        :disabled="store.animationState === 'stopped'"
        @click="handleStop"
        class="control-btn stop-btn"
      >
        停止
      </ElButton>

      <ElButton
        type="info"
        size="large"
        :icon="'Refresh'"
        @click="handleReset"
        class="control-btn reset-btn"
      >
        重置
      </ElButton>
    </div>

    <div class="system-status">
      <h4>系统状态</h4>
      <div class="status-grid">
        <div class="status-item">
          <span class="status-label">运行状态</span>
          <span
            class="status-value"
            :class="{
              'text-success': store.animationState === 'running',
              'text-warning': store.animationState === 'paused',
              'text-info': store.animationState === 'stopped'
            }"
          >
            {{
              store.animationState === 'running'
                ? '运行中'
                : store.animationState === 'paused'
                  ? '已暂停'
                  : '已停止'
            }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">传送带上</span>
          <span class="status-value">{{ store.conveyorComponents.length }} 个</span>
        </div>
        <div class="status-item">
          <span class="status-label">已识别</span>
          <span class="status-value">
            {{ store.sortedComponents.length + store.conveyorComponents.filter(c => c.recognized).length }} 个
          </span>
        </div>
      </div>
    </div>

    <div class="current-process">
      <h4>当前工序</h4>
      <div class="process-list">
        <div
          class="process-item"
          :class="{ active: store.animationState === 'running' }"
        >
          <span class="process-icon">1</span>
          <span class="process-text">送货区域 - 传送带运输</span>
        </div>
        <div
          class="process-item"
          :class="{ active: store.currentRecognizing !== null }"
        >
          <span class="process-icon">2</span>
          <span class="process-text">视觉识别区域 - 摄像头识别</span>
        </div>
        <div
          class="process-item"
          :class="{ active: store.currentSorting !== null }"
        >
          <span class="process-icon">3</span>
          <span class="process-text">分拣区域 - 机械臂分拣</span>
        </div>
        <div
          class="process-item"
          :class="{ active: store.currentRetrieving !== null }"
        >
          <span class="process-icon">4</span>
          <span class="process-text">输出通道 - 取出元器件</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.control-panel {
  background: white;
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.panel-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #303133;
  padding-bottom: 0.8rem;
  border-bottom: 2px solid #f0f2f5;
}

.control-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
}

.control-btn {
  height: 48px;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.start-btn {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  border: none;
}

.pause-btn {
  background: linear-gradient(135deg, #e6a23c 0%, #cf9232 100%);
  border: none;
}

.stop-btn {
  background: linear-gradient(135deg, #f56c6c 0%, #e04040 100%);
  border: none;
}

.reset-btn {
  background: linear-gradient(135deg, #909399 0%, #737780 100%);
  border: none;
}

.system-status {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 1rem;
}

.system-status h4 {
  margin: 0 0 0.8rem 0;
  font-size: 0.95rem;
  color: #606266;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0;
}

.status-label {
  color: #909399;
  font-size: 0.9rem;
}

.status-value {
  font-weight: 600;
  color: #303133;
  font-size: 0.95rem;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-info {
  color: #909399;
}

.current-process {
  flex: 1;
}

.current-process h4 {
  margin: 0 0 0.8rem 0;
  font-size: 0.95rem;
  color: #606266;
}

.process-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.process-item {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s ease;
  opacity: 0.5;
}

.process-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  opacity: 1;
  transform: translateX(4px);
}

.process-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #dcdfe6;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.process-item.active .process-icon {
  background: rgba(255, 255, 255, 0.3);
  color: white;
}

.process-text {
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
