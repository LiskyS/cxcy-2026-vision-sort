<template>
  <div class="sorting-system-container">
    <!-- Header -->
    <el-header class="header">
      <div class="header-content">
        <h1 class="title">电子元器件分拣系统 - 数字孪生</h1>
        <div class="status-indicators">
          <el-tag :type="getStatusType()" size="large">
            {{ getStatusText() }}
          </el-tag>
          <el-tag type="info" size="large" style="margin-left: 10px">
            阶段: {{ getPhaseText() }}
          </el-tag>
        </div>
      </div>
    </el-header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- 3D Scene -->
      <div class="scene-container">
        <div ref="sceneContainer" class="three-scene"></div>
      </div>

      <!-- Control Panel -->
      <div class="control-panel">
        <!-- Sorting Statistics Panel -->
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>分拣统计</span>
              <el-tag type="success" size="small" style="margin-left: 10px">
                实时更新
              </el-tag>
            </div>
          </template>
          <div class="stats-content">
            <div class="stat-item highlight">
              <span class="stat-label">已分拣总数:</span>
              <span class="stat-value large">{{ sortedTotal }}</span>
            </div>
            <el-divider style="margin: 12px 0" />
            <div class="stat-item">
              <span class="stat-label">电容:</span>
              <span class="stat-value capacitor-color">{{ sortedCapacitors }}</span>
              <span class="stat-percent">({{ getPercentage(sortedCapacitors) }}%)</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">端子:</span>
              <span class="stat-value terminal-color">{{ sortedTerminals }}</span>
              <span class="stat-percent">({{ getPercentage(sortedTerminals) }}%)</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">连接器:</span>
              <span class="stat-value connector-color">{{ sortedConnectors }}</span>
              <span class="stat-percent">({{ getPercentage(sortedConnectors) }}%)</span>
            </div>
            <el-divider style="margin: 12px 0" />
            <div class="stat-item">
              <span class="stat-label">传送带上:</span>
              <span class="stat-value">{{ componentsOnBelt }}</span>
            </div>
          </div>
        </el-card>

        <!-- System Control Panel -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统控制</span>
            </div>
          </template>
          <div class="controls">
            <el-button 
              type="success" 
              size="large" 
              :disabled="isRunning && !isPaused"
              @click="handleStart"
            >
              <el-icon><VideoPlay /></el-icon>
              开始
            </el-button>
            
            <el-button 
              type="warning" 
              size="large" 
              :disabled="!isRunning || isPaused"
              @click="handlePause"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            
            <el-button 
              type="primary" 
              size="large" 
              :disabled="!isPaused"
              @click="handleResume"
            >
              <el-icon><CaretRight /></el-icon>
              继续
            </el-button>
            
            <el-button 
              type="danger" 
              size="large" 
              :disabled="!isRunning && !isPaused"
              @click="handleStop"
            >
              <el-icon><SwitchButton /></el-icon>
              停止
            </el-button>
          </div>
        </el-card>

        <!-- Process Description -->
        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>流程说明</span>
            </div>
          </template>
          <div class="process-steps">
            <div 
              v-for="(step, index) in processSteps" 
              :key="index"
              class="step-item"
              :class="{ active: currentPhase === step.phase }"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-desc">{{ step.description }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useSystemStore } from './store/system'
import SortingScene from './three/SortingScene'

const systemStore = useSystemStore()
const sceneContainer = ref(null)
let sortingScene = null

// Use storeToRefs to preserve reactivity when destructuring
const { 
  isRunning, 
  isPaused, 
  currentPhase,
  totalComponents,
  sortedCapacitors,
  sortedTerminals,
  sortedConnectors,
  sortedTotal
} = storeToRefs(systemStore)

// Computed: Components currently on the belt (total - sorted)
const componentsOnBelt = computed(() => {
  return Math.max(0, totalComponents.value - sortedTotal.value)
})

const processSteps = [
  {
    phase: 'delivering',
    title: '送货',
    description: '元器件通过传送带送到识别区域'
  },
  {
    phase: 'identifying',
    title: '识别',
    description: '高清摄像头通过视觉模型识别元器件类型'
  },
  {
    phase: 'sorting',
    title: '分拣',
    description: '机械臂将元器件分拣到不同的输出通道'
  },
  {
    phase: 'picking',
    title: '取货',
    description: '从出口取出元器件并装载到货车中'
  }
]

function getStatusType() {
  if (!isRunning.value) return 'info'
  if (isPaused.value) return 'warning'
  return 'success'
}

function getStatusText() {
  if (!isRunning.value) return '已停止'
  if (isPaused.value) return '已暂停'
  return '运行中'
}

function getPhaseText() {
  const phaseMap = {
    'idle': '空闲',
    'delivering': '送货中',
    'identifying': '识别中',
    'sorting': '分拣中',
    'picking': '取货中'
  }
  return phaseMap[currentPhase.value] || currentPhase.value
}

function getPercentage(count) {
  // In Vue templates, refs are auto-unwrapped, so count is already a number
  const total = sortedTotal.value
  if (!total || total === 0) return '0.0'
  const percentage = (count / total) * 100
  return percentage.toFixed(1)
}

function handleStart() {
  systemStore.start()
  if (sortingScene) {
    sortingScene.start()
  }
}

function handlePause() {
  systemStore.pause()
  if (sortingScene) {
    sortingScene.pause()
  }
}

function handleResume() {
  systemStore.resume()
  if (sortingScene) {
    sortingScene.resume()
  }
}

function handleStop() {
  systemStore.stop()
  if (sortingScene) {
    sortingScene.stop()
  }
}

onMounted(() => {
  if (sceneContainer.value) {
    sortingScene = new SortingScene(sceneContainer.value, systemStore)
    sortingScene.init()
  }
})

onBeforeUnmount(() => {
  if (sortingScene) {
    sortingScene.destroy()
  }
})
</script>

<style scoped>
/* Override Element Plus styles for dark industrial theme */
:deep(.el-card) {
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

:deep(.el-card__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 20px;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-button) {
  font-weight: 500;
}

:deep(.el-tag) {
  border: none;
}

.sorting-system-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
}

.header {
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  padding: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 30px;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
}

.status-indicators {
  display: flex;
  align-items: center;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.scene-container {
  flex: 1;
  position: relative;
  background: #0a0a1a;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card-header {
  font-weight: 600;
  font-size: 16px;
  color: #ffffff;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-item.highlight {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1), rgba(103, 194, 58, 0.1));
  padding: 16px 12px;
  margin: -8px -12px 8px -12px;
  border-radius: 8px;
  border-bottom: none;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: #a0a0b0;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}

.stat-value.large {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-percent {
  font-size: 12px;
  color: #808090;
  margin-left: 8px;
}

.capacitor-color {
  color: #409eff;
}

.terminal-color {
  color: #67c23a;
}

.connector-color {
  color: #e6a23c;
}

.three-scene {
  width: 100%;
  height: 100%;
}

.stats-card {
  margin-bottom: 20px;
}

.control-panel {
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.controls {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.process-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.step-item.active {
  background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
  color: white;
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 210, 255, 0.3);
  border-color: rgba(0, 210, 255, 0.5);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3a7bd5;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.active .step-number {
  background: white;
  color: #3a7bd5;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 12px;
  opacity: 0.8;
  line-height: 1.4;
}

.step-item {
  color: #e0e0e0;
}

.step-item.active {
  color: #ffffff;
}
</style>
