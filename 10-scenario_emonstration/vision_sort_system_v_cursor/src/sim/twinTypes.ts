export type PartType = '电容' | '端子' | '连接器'

export type TwinStatus = 'stopped' | 'running' | 'paused'

export type Vec3 = { x: number; y: number; z: number }

export type SortStats = {
  total: number
  byType: Record<PartType, number>
  lastRecognizedType: PartType | '-'
  lastRecognizedPosition: Vec3
  lastSortedType: PartType | '-'
  lastSortedPosition: Vec3
  // pipeline metrics (feed -> recognize -> sort)
  feedSpawned: number
  feedBlocked: number
  recogQueued: number
  recogDone: number
  sortPicked: number
  qRecognize: number
  qPick: number
}

