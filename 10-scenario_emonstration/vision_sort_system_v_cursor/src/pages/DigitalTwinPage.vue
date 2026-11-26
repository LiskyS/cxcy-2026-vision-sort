<script setup lang="ts">
import { computed } from 'vue'
import { useTwinStore } from '../sim/twinStore'
import ThreeTwinScene from '../views/ThreeTwinScene.vue'
import StatsPanel from '../views/StatsPanel.vue'
import ControlPanel from '../views/ControlPanel.vue'
import { formatVec3 } from '../sim/utils'

const store = useTwinStore()

const statusText = computed(() => {
  if (store.state.status === 'running') return '运行中'
  if (store.state.status === 'paused') return '已暂停'
  return '已停止'
})
</script>

<template>
  <div class="app-shell">
    <div class="app-topbar">
      <div class="app-title">
        <h1>电子元器件视觉分拣数字孪生</h1>
        <div class="subtitle">送货 → 识别 → 分拣 → 取货（Vue3 + Three.js）</div>
      </div>
      <div class="small-muted">
        状态：<b>{{ statusText }}</b>
        <span style="padding: 0 8px">|</span>
        速度：<b>{{ store.state.speed.toFixed(2) }}x</b>
      </div>
    </div>

    <div class="app-body">
      <div class="scene-card">
        <div class="scene-toolbar">
          <div class="hint">
            可视化流程：传送带运送混合元器件 → 摄像头识别 → 机械臂抓取分拣 → 通道出口入箱
          </div>
          <div class="hint">
            最新位置：{{ formatVec3(store.state.lastKnownPosition) }}
          </div>
        </div>
        <div class="scene-wrap">
          <ThreeTwinScene />
        </div>
      </div>

      <div class="sidebar">
        <div class="sidebar-card">
          <div class="card-hd">分拣统计</div>
          <div class="card-bd">
            <StatsPanel />
          </div>
        </div>

        <div class="sidebar-card">
          <div class="card-hd">系统控制</div>
          <div class="card-bd">
            <ControlPanel />
          </div>
        </div>

        <div class="sidebar-card" style="flex: 1; min-height: 0">
          <div class="card-hd">说明</div>
          <div class="card-bd">
            <div class="small-muted" style="line-height: 1.65">
              - 送货区域：元器件混合进入主传送带<br />
              - 识别区域：相机与识别光圈高亮扫描，更新“识别类型/位置”<br />
              - 分拣区域：机械臂运动到抓取点，夹爪下探抓取，再移动到对应输出通道放置<br />
              - 取货区域：通道末端将元器件送入对应货箱并累计数量
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

