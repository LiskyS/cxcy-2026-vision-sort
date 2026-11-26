import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ComponentType = 'capacitor' | 'terminal' | 'connector'

export interface SortedComponent {
  id: number
  type: ComponentType
  position: { x: number; y: number; z: number }
  timestamp: number
  channel: number
}

export interface ConveyorComponent {
  id: number
  type: ComponentType
  position: { x: number; y: number; z: number }
  rotation: { x: number; y: number; z: number }
  state: 'waiting' | 'on_conveyor' | 'recognizing' | 'sorted' | 'retrieved'
  recognized?: boolean
}

export const useSortingStore = defineStore('sorting', () => {
  const animationState = ref<'stopped' | 'running' | 'paused'>('stopped')
  const totalSorted = ref(0)
  const sortedComponents = ref<SortedComponent[]>([])
  const conveyorComponents = ref<ConveyorComponent[]>([])
  const currentRecognizing = ref<ConveyorComponent | null>(null)
  const currentSorting = ref<ConveyorComponent | null>(null)
  const currentRetrieving = ref<ConveyorComponent | null>(null)
  const nextComponentId = ref(1)

  const componentCounts = computed(() => {
    const counts = { capacitor: 0, terminal: 0, connector: 0 }
    sortedComponents.value.forEach(comp => {
      counts[comp.type]++
    })
    return counts
  })

  const channelCounts = computed(() => {
    const counts = { capacitor: 0, terminal: 0, connector: 0 }
    sortedComponents.value.forEach(comp => {
      const typeMap: Record<number, ComponentType> = { 1: 'capacitor', 2: 'terminal', 3: 'connector' }
      const type = typeMap[comp.channel]
      if (type) counts[type]++
    })
    return counts
  })

  function start() {
    if (animationState.value === 'stopped') {
      animationState.value = 'running'
      generateComponents()
    } else if (animationState.value === 'paused') {
      animationState.value = 'running'
    }
  }

  function pause() {
    if (animationState.value === 'running') {
      animationState.value = 'paused'
    }
  }

  function stop() {
    animationState.value = 'stopped'
    conveyorComponents.value = []
    currentRecognizing.value = null
    currentSorting.value = null
    currentRetrieving.value = null
  }

  function generateComponents() {
    const types: ComponentType[] = ['capacitor', 'terminal', 'connector']
    const randomType = types[Math.floor(Math.random() * types.length)]
    const component: ConveyorComponent = {
      id: nextComponentId.value++,
      type: randomType,
      position: { x: -15, y: 0.5, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      state: 'on_conveyor'
    }
    conveyorComponents.value.push(component)
  }

  function addSortedComponent(type: ComponentType, position: { x: number; y: number; z: number }, channel: number) {
    const component: SortedComponent = {
      id: nextComponentId.value++,
      type,
      position,
      timestamp: Date.now(),
      channel
    }
    sortedComponents.value.push(component)
    totalSorted.value++
  }

  function setRecognizing(component: ConveyorComponent | null) {
    currentRecognizing.value = component
  }

  function setSorting(component: ConveyorComponent | null) {
    currentSorting.value = component
  }

  function setRetrieving(component: ConveyorComponent | null) {
    currentRetrieving.value = component
  }

  function updateConveyorComponentPosition(id: number, position: { x: number; y: number; z: number }) {
    const component = conveyorComponents.value.find(c => c.id === id)
    if (component) {
      component.position = position
    }
  }

  function updateConveyorComponentState(id: number, state: ConveyorComponent['state']) {
    const component = conveyorComponents.value.find(c => c.id === id)
    if (component) {
      component.state = state
    }
  }

  function removeConveyorComponent(id: number) {
    const index = conveyorComponents.value.findIndex(c => c.id === id)
    if (index !== -1) {
      conveyorComponents.value.splice(index, 1)
    }
  }

  function reset() {
    animationState.value = 'stopped'
    totalSorted.value = 0
    sortedComponents.value = []
    conveyorComponents.value = []
    currentRecognizing.value = null
    currentSorting.value = null
    currentRetrieving.value = null
    nextComponentId.value = 1
  }

  return {
    animationState,
    totalSorted,
    sortedComponents,
    conveyorComponents,
    currentRecognizing,
    currentSorting,
    currentRetrieving,
    componentCounts,
    channelCounts,
    start,
    pause,
    stop,
    reset,
    generateComponents,
    addSortedComponent,
    setRecognizing,
    setSorting,
    setRetrieving,
    updateConveyorComponentPosition,
    updateConveyorComponentState,
    removeConveyorComponent
  }
})
