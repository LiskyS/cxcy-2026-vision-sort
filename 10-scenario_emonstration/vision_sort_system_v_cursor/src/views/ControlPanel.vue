<script setup lang="ts">
import { computed } from 'vue'
import { ElButton, ElButtonGroup, ElDivider, ElSlider, ElTag } from 'element-plus'
import { useTwinStore } from '../sim/twinStore'

const store = useTwinStore()

const statusLabel = computed(() => {
  if (store.state.status === 'running') return { text: '运行中', type: 'success' as const }
  if (store.state.status === 'paused') return { text: '已暂停', type: 'warning' as const }
  return { text: '已停止', type: 'info' as const }
})
</script>

<template>
  <div style="display: grid; gap: 10px">
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px">
      <div class="small-muted">运行状态</div>
      <ElTag :type="statusLabel.type" effect="light">{{ statusLabel.text }}</ElTag>
    </div>

    <ElButtonGroup>
      <ElButton type="primary" :disabled="store.state.status === 'running'" @click="store.start()">
        开始
      </ElButton>
      <ElButton :disabled="store.state.status !== 'running'" @click="store.pause()">暂停</ElButton>
      <ElButton type="danger" @click="store.stop()">停止</ElButton>
    </ElButtonGroup>

    <ElDivider style="margin: 6px 0" />

    <div style="display: flex; align-items: center; justify-content: space-between">
      <div class="small-muted">动画速度</div>
      <div style="font-weight: 700">{{ store.state.speed.toFixed(2) }}x</div>
    </div>
    <ElSlider
      :min="0.2"
      :max="3"
      :step="0.05"
      :model-value="store.state.speed"
      @update:model-value="store.setSpeed($event as number)"
    />

    <div class="small-muted">
      提示：暂停会冻结流程；停止会重置统计并清空场景内元器件。
    </div>
  </div>
</template>

