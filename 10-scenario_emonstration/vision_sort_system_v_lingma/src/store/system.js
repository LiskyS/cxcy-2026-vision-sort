import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSystemStore = defineStore('system', () => {
  // System status
  const isRunning = ref(false)
  const isPaused = ref(false)
  const currentPhase = ref('idle') // idle, delivering, identifying, sorting, picking
  
  // Statistics
  const totalComponents = ref(0)
  const sortedCapacitors = ref(0)
  const sortedTerminals = ref(0)
  const sortedConnectors = ref(0)
  
  // Computed
  const sortedTotal = computed(() => 
    sortedCapacitors.value + sortedTerminals.value + sortedConnectors.value
  )
  
  // Actions
  function start() {
    isRunning.value = true
    isPaused.value = false
    currentPhase.value = 'delivering'
  }
  
  function pause() {
    isPaused.value = true
  }
  
  function resume() {
    isPaused.value = false
  }
  
  function stop() {
    isRunning.value = false
    isPaused.value = false
    currentPhase.value = 'idle'
    totalComponents.value = 0
    sortedCapacitors.value = 0
    sortedTerminals.value = 0
    sortedConnectors.value = 0
  }
  
  function setPhase(phase) {
    currentPhase.value = phase
  }
  
  function incrementComponent(type) {
    console.log('Store: incrementComponent called with type:', type)
    console.log('Store: Before - totalComponents:', totalComponents.value, 'sortedCapacitors:', sortedCapacitors.value, 'sortedTerminals:', sortedTerminals.value, 'sortedConnectors:', sortedConnectors.value)
    
    totalComponents.value++
    if (type === 'capacitor') {
      sortedCapacitors.value++
    } else if (type === 'terminal') {
      sortedTerminals.value++
    } else if (type === 'connector') {
      sortedConnectors.value++
    }
    
    console.log('Store: After - totalComponents:', totalComponents.value, 'sortedCapacitors:', sortedCapacitors.value, 'sortedTerminals:', sortedTerminals.value, 'sortedConnectors:', sortedConnectors.value)
  }
  
  return {
    isRunning,
    isPaused,
    currentPhase,
    totalComponents,
    sortedCapacitors,
    sortedTerminals,
    sortedConnectors,
    sortedTotal,
    start,
    pause,
    resume,
    stop,
    setPhase,
    incrementComponent
  }
})
