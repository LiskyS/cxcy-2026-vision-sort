<script setup lang="ts">
import { computed } from 'vue'
import { useTwinStore } from '../sim/twinStore'
import { formatVec3 } from '../sim/utils'

const store = useTwinStore()
const s = computed(() => store.state.stats)
</script>

<template>
  <div class="kv">
    <div class="k">上料数</div>
    <div class="v">{{ s.feedSpawned }}</div>

    <div class="k">上料阻塞</div>
    <div class="v">{{ s.feedBlocked }}</div>

    <div class="k">识别排队</div>
    <div class="v">{{ s.qRecognize }}（累计入队 {{ s.recogQueued }} / 完成 {{ s.recogDone }}）</div>

    <div class="k">分拣排队</div>
    <div class="v">{{ s.qPick }}（已抓取 {{ s.sortPicked }}）</div>

    <div class="k">累计分拣</div>
    <div class="v">{{ s.total }}</div>

    <div class="k">电容通道</div>
    <div class="v">{{ s.byType['电容'] }}</div>

    <div class="k">端子通道</div>
    <div class="v">{{ s.byType['端子'] }}</div>

    <div class="k">连接器通道</div>
    <div class="v">{{ s.byType['连接器'] }}</div>

    <div class="k">最新识别类型</div>
    <div class="v">{{ s.lastRecognizedType }}</div>

    <div class="k">最新识别位置</div>
    <div class="v">{{ formatVec3(s.lastRecognizedPosition) }}</div>

    <div class="k">最新分拣类型</div>
    <div class="v">{{ s.lastSortedType }}</div>

    <div class="k">最新分拣位置</div>
    <div class="v">{{ formatVec3(s.lastSortedPosition) }}</div>
  </div>
</template>

