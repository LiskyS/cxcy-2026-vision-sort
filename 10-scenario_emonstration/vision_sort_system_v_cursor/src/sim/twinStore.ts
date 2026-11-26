import { reactive } from 'vue'
import type { PartType, SortStats, TwinStatus, Vec3 } from './twinTypes'
import { cloneVec3, vec3 } from './utils'

type TwinState = {
  status: TwinStatus
  speed: number
  tick: number
  stats: SortStats
  lastKnownPosition: Vec3
}

const initialStats = (): SortStats => ({
  total: 0,
  byType: { 电容: 0, 端子: 0, 连接器: 0 },
  lastRecognizedType: '-',
  lastRecognizedPosition: vec3(),
  lastSortedType: '-',
  lastSortedPosition: vec3(),
  feedSpawned: 0,
  feedBlocked: 0,
  recogQueued: 0,
  recogDone: 0,
  sortPicked: 0,
  qRecognize: 0,
  qPick: 0,
})

const state = reactive<TwinState>({
  status: 'stopped',
  speed: 1,
  tick: 0,
  stats: initialStats(),
  lastKnownPosition: vec3(),
})

export function useTwinStore() {
  const start = () => {
    state.status = 'running'
  }

  const pause = () => {
    if (state.status === 'running') state.status = 'paused'
  }

  const stop = () => {
    state.status = 'stopped'
    state.tick = 0
    state.stats = initialStats()
    state.lastKnownPosition = vec3()
  }

  const setSpeed = (speed: number) => {
    state.speed = Math.max(0.2, Math.min(3, speed))
  }

  const markRecognized = (type: PartType, pos: Vec3) => {
    state.stats.recogDone += 1
    state.stats.lastRecognizedType = type
    state.stats.lastRecognizedPosition = cloneVec3(pos)
    state.lastKnownPosition = cloneVec3(pos)
  }

  const markSorted = (type: PartType, pos: Vec3) => {
    state.stats.total += 1
    state.stats.byType[type] += 1
    state.stats.lastSortedType = type
    state.stats.lastSortedPosition = cloneVec3(pos)
    state.lastKnownPosition = cloneVec3(pos)
  }

  const markFeedSpawned = () => {
    state.stats.feedSpawned += 1
  }

  const markFeedBlocked = () => {
    state.stats.feedBlocked += 1
  }

  const markRecogQueued = () => {
    state.stats.recogQueued += 1
  }

  const markSortPicked = () => {
    state.stats.sortPicked += 1
  }

  const setQueues = (qRecognize: number, qPick: number) => {
    state.stats.qRecognize = qRecognize
    state.stats.qPick = qPick
  }

  const updateLastKnown = (pos: Vec3) => {
    state.lastKnownPosition = cloneVec3(pos)
  }

  return {
    state,
    start,
    pause,
    stop,
    setSpeed,
    markRecognized,
    markSorted,
    markFeedSpawned,
    markFeedBlocked,
    markRecogQueued,
    markSortPicked,
    setQueues,
    updateLastKnown,
  }
}

