<script setup lang="ts">
import { onMounted } from 'vue'
import { useSortingStore } from '../stores/sortingStore'
import ThreeScene from '../components/ThreeScene.vue'
import ControlPanel from '../components/ControlPanel.vue'
import StatisticsPanel from '../components/StatisticsPanel.vue'

const store = useSortingStore()

onMounted(() => {
  document.body.classList.add('light-theme')
})
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>电子元器件智能分拣系统</h1>
      <p class="subtitle">Vision-Based Electronic Component Sorting System</p>
    </header>

    <main class="app-main">
      <aside class="sidebar-left">
        <StatisticsPanel />
      </aside>

      <section class="scene-container">
        <ThreeScene />
        <div class="scene-overlay">
          <div class="status-indicator">
            <span
              class="status-dot"
              :class="{
                'status-running': store.animationState === 'running',
                'status-paused': store.animationState === 'paused',
                'status-stopped': store.animationState === 'stopped'
              }"
            ></span>
            <span class="status-text">
              {{ store.animationState === 'running' ? '运行中' : store.animationState === 'paused' ? '已暂停' : '已停止' }}
            </span>
          </div>
        </div>
      </section>

      <aside class="sidebar-right">
        <ControlPanel />
      </aside>
    </main>

    <footer class="app-footer">
      <div class="legend">
        <div class="legend-item">
          <span class="legend-color capacitor"></span>
          <span>电容</span>
        </div>
        <div class="legend-item">
          <span class="legend-color terminal"></span>
          <span>端子</span>
        </div>
        <div class="legend-item">
          <span class="legend-color connector"></span>
          <span>连接器</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.app-header .subtitle {
  margin: 0.3rem 0 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.app-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 1rem;
  padding: 1rem;
}

.sidebar-left,
.sidebar-right {
  width: 280px;
  display: flex;
  flex-direction: column;
}

.scene-container {
  flex: 1;
  position: relative;
  background: linear-gradient(180deg, #ffffff 0%, #f0f2f5 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.scene-overlay {
  position: absolute;
  top: 1rem;
  left: 1rem;
  z-index: 10;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.6rem 1rem;
  border-radius: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-running {
  background: #67c23a;
}

.status-paused {
  background: #e6a23c;
  animation: none;
}

.status-stopped {
  background: #909399;
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 0.9rem;
  font-weight: 500;
  color: #303133;
}

.app-footer {
  padding: 0.8rem 2rem;
  background: white;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #606266;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.legend-color.capacitor {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.legend-color.terminal {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}

.legend-color.connector {
  background: linear-gradient(135deg, #e6a23c 0%, #cf9232 100%);
}
</style>
