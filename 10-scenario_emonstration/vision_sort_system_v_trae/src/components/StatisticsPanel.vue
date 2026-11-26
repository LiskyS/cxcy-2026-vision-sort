<script setup lang="ts">
import { useSortingStore } from '../stores/sortingStore'
import { ElCard, ElProgress } from 'element-plus'

const store = useSortingStore()
</script>

<template>
  <div class="statistics-panel">
    <h3 class="panel-title">分拣统计</h3>

    <ElCard class="total-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>总分拣数量</span>
        </div>
      </template>
      <div class="total-statistic">
        <span class="total-number">{{ store.totalSorted }}</span>
        <span class="total-unit">个</span>
      </div>
    </ElCard>

    <ElCard class="type-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>元器件类型统计</span>
        </div>
      </template>
      <div class="type-stats">
        <div class="type-item">
          <div class="type-header">
            <span class="type-name">电容</span>
            <span class="type-count">{{ store.componentCounts.capacitor }} 个</span>
          </div>
          <ElProgress
            :percentage="store.totalSorted > 0 ? (store.componentCounts.capacitor / store.totalSorted) * 100 : 0"
            :stroke-width="10"
            :show-text="false"
            color="#409eff"
          />
        </div>
        <div class="type-item">
          <div class="type-header">
            <span class="type-name">端子</span>
            <span class="type-count">{{ store.componentCounts.terminal }} 个</span>
          </div>
          <ElProgress
            :percentage="store.totalSorted > 0 ? (store.componentCounts.terminal / store.totalSorted) * 100 : 0"
            :stroke-width="10"
            :show-text="false"
            color="#67c23a"
          />
        </div>
        <div class="type-item">
          <div class="type-header">
            <span class="type-name">连接器</span>
            <span class="type-count">{{ store.componentCounts.connector }} 个</span>
          </div>
          <ElProgress
            :percentage="store.totalSorted > 0 ? (store.componentCounts.connector / store.totalSorted) * 100 : 0"
            :stroke-width="10"
            :show-text="false"
            color="#e6a23c"
          />
        </div>
      </div>
    </ElCard>

    <ElCard class="channel-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>通道统计</span>
        </div>
      </template>
      <div class="channel-stats">
        <div class="channel-item capacitor">
          <div class="channel-info">
            <span class="channel-name">电容通道</span>
            <span class="channel-count">{{ store.channelCounts.capacitor }} 个</span>
          </div>
          <div class="channel-bar">
            <div
              class="channel-fill"
              :style="{ width: (store.channelCounts.capacitor / Math.max(store.totalSorted, 1)) * 100 + '%' }"
            ></div>
          </div>
        </div>
        <div class="channel-item terminal">
          <div class="channel-info">
            <span class="channel-name">端子通道</span>
            <span class="channel-count">{{ store.channelCounts.terminal }} 个</span>
          </div>
          <div class="channel-bar">
            <div
              class="channel-fill"
              :style="{ width: (store.channelCounts.terminal / Math.max(store.totalSorted, 1)) * 100 + '%' }"
            ></div>
          </div>
        </div>
        <div class="channel-item connector">
          <div class="channel-info">
            <span class="channel-name">连接器通道</span>
            <span class="channel-count">{{ store.channelCounts.connector }} 个</span>
          </div>
          <div class="channel-bar">
            <div
              class="channel-fill"
              :style="{ width: (store.channelCounts.connector / Math.max(store.totalSorted, 1)) * 100 + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </ElCard>

    <ElCard class="recent-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近分拣记录</span>
        </div>
      </template>
      <div class="recent-list">
        <div
          v-for="comp in store.sortedComponents.slice(-5).reverse()"
          :key="comp.id"
          class="recent-item"
        >
          <span
            class="recent-type"
            :class="comp.type"
          >
            {{ comp.type === 'capacitor' ? '电容' : comp.type === 'terminal' ? '端子' : '连接器' }}
          </span>
          <span class="recent-channel">
            通道 {{ comp.channel }}
          </span>
          <span class="recent-pos">
            ({{ comp.position.x.toFixed(1) }}, {{ comp.position.z.toFixed(1) }})
          </span>
        </div>
        <div v-if="store.sortedComponents.length === 0" class="no-data">
          暂无分拣记录
        </div>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.statistics-panel {
  background: white;
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.panel-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #303133;
  padding-bottom: 0.8rem;
  border-bottom: 2px solid #f0f2f5;
}

:deep(.el-card) {
  border-radius: 12px;
  border: none;
}

:deep(.el-card__header) {
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #f0f2f5;
}

:deep(.el-card__body) {
  padding: 1rem;
}

.card-header {
  font-size: 0.95rem;
  font-weight: 600;
  color: #606266;
}

.total-card :deep(.el-card__body) {
  text-align: center;
  padding: 1.5rem;
}

.total-statistic {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.3rem;
}

.total-number {
  font-size: 3rem;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.total-unit {
  font-size: 1.2rem;
  color: #909399;
}

.type-stats {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.type-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-name {
  font-size: 0.9rem;
  color: #606266;
}

.type-count {
  font-size: 0.9rem;
  font-weight: 600;
  color: #303133;
}

:deep(.el-progress-bar__outer) {
  border-radius: 5px;
}

.channel-stats {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.channel-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.channel-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-name {
  font-size: 0.85rem;
  color: #606266;
}

.channel-count {
  font-size: 0.85rem;
  font-weight: 600;
}

.channel-item.capacitor .channel-name,
.channel-item.capacitor .channel-count {
  color: #409eff;
}

.channel-item.terminal .channel-name,
.channel-item.terminal .channel-count {
  color: #67c23a;
}

.channel-item.connector .channel-name,
.channel-item.connector .channel-count {
  color: #e6a23c;
}

.channel-bar {
  height: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.channel-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.channel-item.capacitor .channel-fill {
  background: linear-gradient(90deg, #409eff, #66b1ff);
}

.channel-item.terminal .channel-fill {
  background: linear-gradient(90deg, #67c23a, #85ce61);
}

.channel-item.connector .channel-fill {
  background: linear-gradient(90deg, #e6a23c, #ebb563);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 0.85rem;
}

.recent-type {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.recent-type.capacitor {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.recent-type.terminal {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.recent-type.connector {
  background: rgba(230, 162, 60, 0.15);
  color: #e6a23c;
}

.recent-channel {
  color: #606266;
  font-weight: 500;
}

.recent-pos {
  color: #909399;
  font-size: 0.8rem;
  margin-left: auto;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 1rem;
  font-size: 0.9rem;
}
</style>
