<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { useSortingStore, type ComponentType, type ConveyorComponent } from '../stores/sortingStore'

const containerRef = ref<HTMLDivElement | null>(null)
const store = useSortingStore()

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let clock: THREE.Clock

const conveyorBelt: THREE.Group = new THREE.Group()
const conveyorItems: THREE.Group = new THREE.Group()
const roboticArm: THREE.Group = new THREE.Group()
const outputChannels: THREE.Group = new THREE.Group()
const cartonsGroup: THREE.Group = new THREE.Group()

const components3D: Map<number, THREE.Group> = new Map()

const recognitionLight: THREE.PointLight = new THREE.PointLight(0x409eff, 2, 10)
let recognitionBeam: THREE.Mesh

let animationPhase: 'idle' | 'conveyor' | 'recognition' | 'sorting' | 'retrieval' = 'idle'
let currentPhaseTime = 0
let activeSortingComponent: ConveyorComponent | null = null
let retrievedComponents: SortedComponentData[] = []

interface SortedComponentData {
  type: ComponentType
  channel: number
  y: number
}

const channelXPositions = { capacitor: -6, terminal: 0, connector: 6 }

function createConveyorBelt() {
  const beltGroup = new THREE.Group()

  const beltGeometry = new THREE.BoxGeometry(30, 0.3, 3)
  const beltMaterial = new THREE.MeshStandardMaterial({
    color: 0x2c2c2c,
    roughness: 0.8,
    metalness: 0.2
  })
  const belt = new THREE.Mesh(beltGeometry, beltMaterial)
  belt.position.y = 0.15
  beltGroup.add(belt)

  const sideGeometry = new THREE.BoxGeometry(30, 0.5, 0.2)
  const sideMaterial = new THREE.MeshStandardMaterial({ color: 0x409eff, metalness: 0.5, roughness: 0.3 })

  const leftSide = new THREE.Mesh(sideGeometry, sideMaterial)
  leftSide.position.set(0, 0.4, 1.6)
  beltGroup.add(leftSide)

  const rightSide = new THREE.Mesh(sideGeometry, sideMaterial)
  rightSide.position.set(0, 0.4, -1.6)
  beltGroup.add(rightSide)

  const legGeometry = new THREE.CylinderGeometry(0.1, 0.1, 1, 8)
  const legMaterial = new THREE.MeshStandardMaterial({ color: 0x606266, metalness: 0.7, roughness: 0.3 })
  const legPositions = [-12, -6, 0, 6, 12]

  legPositions.forEach(x => {
    const leg = new THREE.Mesh(legGeometry, legMaterial)
    leg.position.set(x, -0.35, 1.2)
    beltGroup.add(leg)
    const leg2 = new THREE.Mesh(legGeometry, legMaterial)
    leg2.position.set(x, -0.35, -1.2)
    beltGroup.add(leg2)
  })

  const rollGeometry = new THREE.CylinderGeometry(0.4, 0.4, 3.2, 16)
  const rollMaterial = new THREE.MeshStandardMaterial({ color: 0x909399, metalness: 0.6, roughness: 0.4 })

  const roll1 = new THREE.Mesh(rollGeometry, rollMaterial)
  roll1.rotation.x = Math.PI / 2
  roll1.position.set(-14.5, 0.3, 0)
  roll1.userData.type = 'roller'
  roll1.userData.speed = 0
  beltGroup.add(roll1)

  const roll2 = new THREE.Mesh(rollGeometry, rollMaterial)
  roll2.rotation.x = Math.PI / 2
  roll2.position.set(14.5, 0.3, 0)
  roll2.userData.type = 'roller'
  roll2.userData.speed = 0
  beltGroup.add(roll2)

  beltGroup.userData.rollers = [roll1, roll2]
  return beltGroup
}

function createComponent3D(type: ComponentType): THREE.Group {
  const group = new THREE.Group()
  let material: THREE.MeshStandardMaterial

  switch (type) {
    case 'capacitor':
      const bodyGeom = new THREE.CylinderGeometry(0.25, 0.25, 0.6, 16)
      material = new THREE.MeshStandardMaterial({ color: 0x409eff, metalness: 0.3, roughness: 0.6 })
      const body = new THREE.Mesh(bodyGeom, material)
      group.add(body)

      const leadGeom = new THREE.CylinderGeometry(0.03, 0.03, 0.4, 8)
      const leadMat = new THREE.MeshStandardMaterial({ color: 0xc0c4cc, metalness: 0.8, roughness: 0.2 })
      const lead1 = new THREE.Mesh(leadGeom, leadMat)
      lead1.position.y = -0.5
      group.add(lead1)
      const lead2 = new THREE.Mesh(leadGeom, leadMat)
      lead2.position.y = -0.5
      lead2.position.x = 0.3
      group.add(lead2)
      break

    case 'terminal':
      const baseGeom = new THREE.BoxGeometry(0.6, 0.15, 0.4)
      material = new THREE.MeshStandardMaterial({ color: 0x67c23a, metalness: 0.4, roughness: 0.5 })
      const base = new THREE.Mesh(baseGeom, material)
      group.add(base)

      const pinGeom = new THREE.CylinderGeometry(0.05, 0.05, 0.5, 8)
      const pinMat = new THREE.MeshStandardMaterial({ color: 0xc0c4cc, metalness: 0.8, roughness: 0.2 })
      for (let i = 0; i < 3; i++) {
        const pin = new THREE.Mesh(pinGeom, pinMat)
        pin.position.set(-0.2 + i * 0.2, -0.3, 0)
        group.add(pin)
      }
      break

    case 'connector':
      const housingGeom = new THREE.BoxGeometry(0.8, 0.4, 0.5)
      material = new THREE.MeshStandardMaterial({ color: 0xe6a23c, metalness: 0.3, roughness: 0.6 })
      const housing = new THREE.Mesh(housingGeom, material)
      group.add(housing)

      const slotGeom = new THREE.BoxGeometry(0.15, 0.3, 0.1)
      const slotMat = new THREE.MeshStandardMaterial({ color: 0x303133, metalness: 0.5, roughness: 0.7 })
      for (let i = 0; i < 4; i++) {
        const slot = new THREE.Mesh(slotGeom, slotMat)
        slot.position.set(-0.3 + i * 0.2, 0, 0.3)
        group.add(slot)
      }
      break
  }

  return group
}

function createRecognitionArea() {
  const group = new THREE.Group()

  const frameGeom = new THREE.BoxGeometry(4, 3, 2)
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x909399,
    transparent: true,
    opacity: 0.3,
    metalness: 0.5,
    roughness: 0.5
  })
  const frame = new THREE.Mesh(frameGeom, frameMat)
  group.add(frame)

  const borderGeom = new THREE.EdgesGeometry(frameGeom)
  const borderMat = new THREE.LineBasicMaterial({ color: 0x409eff, linewidth: 2 })
  const border = new THREE.LineSegments(borderGeom, borderMat)
  group.add(border)

  const cameraGeom = new THREE.BoxGeometry(0.6, 0.4, 0.3)
  const cameraMat = new THREE.MeshStandardMaterial({ color: 0x303133, metalness: 0.6, roughness: 0.4 })
  const cameraBody = new THREE.Mesh(cameraGeom, cameraMat)
  cameraBody.position.set(0, 1.2, 0.8)
  group.add(cameraBody)

  const lensGeom = new THREE.CylinderGeometry(0.1, 0.12, 0.15, 16)
  const lensMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, metalness: 0.9, roughness: 0.1 })
  const lens = new THREE.Mesh(lensGeom, lensMat)
  lens.rotation.x = Math.PI / 2
  lens.position.set(0, 1.2, 0.95)
  group.add(lens)

  recognitionLight.position.set(0, 1.5, 1)
  group.add(recognitionLight)

  const beamGeom = new THREE.ConeGeometry(1.5, 3, 32, 1, true)
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0x409eff,
    transparent: true,
    opacity: 0.15,
    side: THREE.DoubleSide
  })
  const beam = new THREE.Mesh(beamGeom, beamMat)
  beam.rotation.x = Math.PI / 2
  beam.position.set(0, 1.2, -0.5)
  group.add(beam)
  recognitionBeam = beam

  group.position.set(0, 1.5, 0)
  return group
}

function createRoboticArm(): THREE.Group {
  const group = new THREE.Group()

  const baseGeom = new THREE.CylinderGeometry(0.5, 0.6, 0.3, 16)
  const baseMat = new THREE.MeshStandardMaterial({ color: 0x303133, metalness: 0.7, roughness: 0.3 })
  const base = new THREE.Mesh(baseGeom, baseMat)
  group.add(base)

  const columnGeom = new THREE.CylinderGeometry(0.15, 0.2, 2.5, 12)
  const columnMat = new THREE.MeshStandardMaterial({ color: 0x409eff, metalness: 0.5, roughness: 0.4 })
  const column = new THREE.Mesh(columnGeom, columnMat)
  column.position.y = 1.4
  group.add(column)

  const armGeom = new THREE.BoxGeometry(2, 0.2, 0.2)
  const armMat = new THREE.MeshStandardMaterial({ color: 0x606266, metalness: 0.6, roughness: 0.4 })
  const arm = new THREE.Mesh(armGeom, armMat)
  arm.position.y = 2.7
  arm.rotation.z = Math.PI / 2
  group.add(arm)

  const wristGeom = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 12)
  const wrist = new THREE.Mesh(wristGeom, armMat)
  wrist.position.set(1, 2.7, 0)
  wrist.rotation.z = Math.PI / 2
  group.add(wrist)

  const gripperGroup = new THREE.Group()

  const palmGeom = new THREE.BoxGeometry(0.3, 0.15, 0.4)
  const palm = new THREE.Mesh(palmGeom, baseMat)
  gripperGroup.add(palm)

  const fingerGeom = new THREE.BoxGeometry(0.08, 0.35, 0.15)
  const finger1 = new THREE.Mesh(fingerGeom, armMat)
  finger1.position.set(0.12, -0.2, 0.1)
  gripperGroup.add(finger1)

  const finger2 = new THREE.Mesh(fingerGeom, armMat)
  finger2.position.set(-0.12, -0.2, 0.1)
  gripperGroup.add(finger2)

  const finger3 = new THREE.Mesh(fingerGeom, armMat)
  finger3.position.set(0.12, -0.2, -0.1)
  gripperGroup.add(finger3)

  const finger4 = new THREE.Mesh(fingerGeom, armMat)
  finger4.position.set(-0.12, -0.2, -0.1)
  gripperGroup.add(finger4)

  gripperGroup.position.set(1.3, 2.7, 0)
  gripperGroup.userData.isGripper = true
  group.add(gripperGroup)

  group.position.set(0, 0.3, 3)
  return group
}

function createOutputChannels(): THREE.Group {
  const group = new THREE.Group()

  const channelColors: Record<ComponentType, number> = {
    capacitor: 0x409eff,
    terminal: 0x67c23a,
    connector: 0xe6a23c
  }
  const labels: Record<ComponentType, string> = {
    capacitor: '电容',
    terminal: '端子',
    connector: '连接器'
  }
  const xPositions: Record<ComponentType, number> = {
    capacitor: -6,
    terminal: 0,
    connector: 6
  }

  const types: ComponentType[] = ['capacitor', 'terminal', 'connector']

  types.forEach((type) => {
    const channelGroup = new THREE.Group()

    const chuteGeom = new THREE.BoxGeometry(2, 0.2, 2)
    const chuteMat = new THREE.MeshStandardMaterial({
      color: channelColors[type],
      metalness: 0.4,
      roughness: 0.6,
      transparent: true,
      opacity: 0.8
    })
    const chute = new THREE.Mesh(chuteGeom, chuteMat)
    chute.position.y = 0.1
    channelGroup.add(chute)

    const dividerGeom = new THREE.BoxGeometry(0.15, 1.5, 0.15)
    const dividerMat = new THREE.MeshStandardMaterial({ color: 0x303133, metalness: 0.6, roughness: 0.4 })

    const leftDivider = new THREE.Mesh(dividerGeom, dividerMat)
    leftDivider.position.set(-0.925, 0.75, 0)
    channelGroup.add(leftDivider)

    const rightDivider = new THREE.Mesh(dividerGeom, dividerMat)
    rightDivider.position.set(0.925, 0.75, 0)
    channelGroup.add(rightDivider)

    const cartonGeom = new THREE.BoxGeometry(1.6, 0.8, 1.6)
    const cartonMat = new THREE.MeshStandardMaterial({
      color: 0xf5f5f5,
      metalness: 0.1,
      roughness: 0.9
    })
    const carton = new THREE.Mesh(cartonGeom, cartonMat)
    carton.position.set(0, 0.5, -2)
    carton.userData.cartonY = 0.5
    channelGroup.add(carton)

    const cartonInnerGeom = new THREE.BoxGeometry(1.4, 0.6, 1.4)
    const cartonInnerMat = new THREE.MeshStandardMaterial({
      color: channelColors[type],
      transparent: true,
      opacity: 0.2
    })
    const cartonInner = new THREE.Mesh(cartonInnerGeom, cartonInnerMat)
    cartonInner.position.set(0, 0.5, -2)
    channelGroup.add(cartonInner)

    channelGroup.position.set(xPositions[type], 0, -8)

    const labelCanvas = document.createElement('canvas')
    labelCanvas.width = 256
    labelCanvas.height = 64
    const ctx = labelCanvas.getContext('2d')!
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, 256, 64)
    ctx.fillStyle = `#${channelColors[type].toString(16)}`
    ctx.font = 'bold 32px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(labels[type], 128, 32)

    const labelTexture = new THREE.CanvasTexture(labelCanvas)
    const labelMat = new THREE.SpriteMaterial({ map: labelTexture })
    const label = new THREE.Sprite(labelMat)
    label.scale.set(2, 0.5, 1)
    label.position.set(0, 1.8, 0)
    channelGroup.add(label)

    group.add(channelGroup)
  })

  return group
}

function initScene() {
  if (!containerRef.value) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f2f5)

  camera = new THREE.PerspectiveCamera(
    60,
    containerRef.value.clientWidth / containerRef.value.clientHeight,
    0.1,
    1000
  )
  camera.position.set(0, 12, 20)
  camera.lookAt(0, 0, -2)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  containerRef.value.appendChild(renderer.domElement)

  clock = new THREE.Clock()

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const mainLight = new THREE.DirectionalLight(0xffffff, 0.8)
  mainLight.position.set(10, 20, 10)
  mainLight.castShadow = true
  mainLight.shadow.mapSize.width = 2048
  mainLight.shadow.mapSize.height = 2048
  mainLight.shadow.camera.near = 0.5
  mainLight.shadow.camera.far = 50
  mainLight.shadow.camera.left = -20
  mainLight.shadow.camera.right = 20
  mainLight.shadow.camera.top = 20
  mainLight.shadow.camera.bottom = -20
  scene.add(mainLight)

  const fillLight = new THREE.DirectionalLight(0xffffff, 0.3)
  fillLight.position.set(-10, 10, -10)
  scene.add(fillLight)

  const conveyorBeltObj = createConveyorBelt()
  conveyorBelt.add(conveyorBeltObj)
  scene.add(conveyorBelt)

  scene.add(conveyorItems)

  const recognitionArea = createRecognitionArea()
  recognitionArea.position.set(0, 0.3, 0)
  scene.add(recognitionArea)

  const arm = createRoboticArm()
  roboticArm.add(arm)
  scene.add(roboticArm)

  const channels = createOutputChannels()
  outputChannels.add(channels)
  scene.add(outputChannels)

  scene.add(cartonsGroup)

  const groundGeom = new THREE.PlaneGeometry(50, 50)
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0xe4e7ed,
    metalness: 0.1,
    roughness: 0.9
  })
  const ground = new THREE.Mesh(groundGeom, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.8
  ground.receiveShadow = true
  scene.add(ground)

  const gridHelper = new THREE.GridHelper(50, 50, 0xdcdef0, 0xdcdef0)
  gridHelper.position.y = -0.79
  scene.add(gridHelper)

  window.addEventListener('resize', onWindowResize)
}

function onWindowResize() {
  if (!containerRef.value) return
  camera.aspect = containerRef.value.clientWidth / containerRef.value.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight)
}

function animate() {
  animationId = requestAnimationFrame(animate)

  const delta = clock.getDelta()

  if (store.animationState === 'running') {
    updateAnimation(delta)
  }

  updateConveyorAnimation(delta)
  updateRoboticArmAnimation()

  renderer.render(scene, camera)
}

function updateConveyorAnimation(delta: number) {
  const rollers = conveyorBelt.children[0].userData.rollers as THREE.Mesh[]
  if (rollers && rollers.length > 0) {
    const speed = store.animationState === 'running' ? 2 : 0
    rollers.forEach(roller => {
      roller.rotation.z += speed * delta
    })
  }
}

function updateAnimation(delta: number) {
  currentPhaseTime += delta

  switch (animationPhase) {
    case 'idle':
      if (currentPhaseTime > 1) {
        if (store.conveyorComponents.length === 0) {
          store.generateComponents()
        }
        animationPhase = 'conveyor'
        currentPhaseTime = 0
      }
      break

    case 'conveyor':
      updateConveyorPhase(delta)
      break

    case 'recognition':
      updateRecognitionPhase()
      break

    case 'sorting':
      updateSortingPhase(delta)
      break

    case 'retrieval':
      updateRetrievalPhase(delta)
      break
  }
}

function updateConveyorPhase(delta: number) {
  const moveSpeed = 3
  const recognitionX = 0

  store.conveyorComponents.forEach(comp => {
    if (comp.state === 'on_conveyor') {
      comp.position.x += moveSpeed * delta

      const comp3D = components3D.get(comp.id)
      if (comp3D) {
        comp3D.position.x = comp.position.x
        comp3D.rotation.y += delta * 0.5
      }

      if (comp.position.x >= recognitionX && !comp.recognized) {
        comp.state = 'recognizing'
        store.setRecognizing(comp)
        animationPhase = 'recognition'
        currentPhaseTime = 0
      }
    }
  })

  if (animationPhase === 'conveyor' && currentPhaseTime > 3) {
    const nextComp = store.conveyorComponents.find(c => c.state === 'on_conveyor' && !c.recognized)
    if (nextComp) {
      store.setRecognizing(nextComp)
      animationPhase = 'recognition'
      currentPhaseTime = 0
    }
  }
}

function updateRecognitionPhase() {
  const comp = store.currentRecognizing
  if (!comp) {
    animationPhase = 'conveyor'
    currentPhaseTime = 0
    return
  }

  recognitionLight.intensity = 2 + Math.sin(currentPhaseTime * 10) * 1.5
  if (recognitionBeam && recognitionBeam.material instanceof THREE.Material) {
    (recognitionBeam.material as THREE.MeshBasicMaterial).opacity = 0.15 + Math.sin(currentPhaseTime * 10) * 0.1
  }

  if (currentPhaseTime > 1.5) {
    comp.recognized = true
    comp.state = 'sorted'
    store.setRecognizing(null)
    activeSortingComponent = comp
    store.setSorting(comp)

    recognitionLight.intensity = 2
    if (recognitionBeam && recognitionBeam.material instanceof THREE.Material) {
      (recognitionBeam.material as THREE.MeshBasicMaterial).opacity = 0.15
    }

    animationPhase = 'sorting'
    currentPhaseTime = 0
  }
}

function updateSortingPhase(delta: number) {
  const comp = activeSortingComponent
  if (!comp) {
    animationPhase = 'retrieval'
    currentPhaseTime = 0
    return
  }

  const comp3D = components3D.get(comp.id)
  if (!comp3D) {
    animationPhase = 'retrieval'
    currentPhaseTime = 0
    return
  }

  const channelX = channelXPositions[comp.type]
  const targetY = 2.5
  const targetZ = -7

  const speed = 5 * delta

  if (Math.abs(comp3D.position.x - channelX) > 0.1) {
    comp3D.position.x += channelX > comp3D.position.x ? speed : -speed
  }

  if (Math.abs(comp3D.position.y - targetY) > 0.1) {
    comp3D.position.y += targetY > comp3D.position.y ? speed : -speed
  }

  if (Math.abs(comp3D.position.z - targetZ) > 0.1) {
    comp3D.position.z += targetZ > comp3D.position.z ? speed : -speed
  }

  const gripper = roboticArm.children[0].children.find(c => c.userData.isGripper)
  if (gripper) {
    const targetArmX = channelX
    const currentArmX = roboticArm.position.x
    if (Math.abs(currentArmX - targetArmX) > 0.1) {
      roboticArm.position.x += channelX > currentArmX ? speed : -speed
    }
    gripper.position.x = roboticArm.position.x + 1.3
    gripper.position.y = 3
  }

  if (
    Math.abs(comp3D.position.x - channelX) < 0.1 &&
    Math.abs(comp3D.position.y - targetY) < 0.1 &&
    Math.abs(comp3D.position.z - targetZ) < 0.1
  ) {
    comp3D.position.set(channelX, 0.3, -7)
    comp3D.rotation.set(0, 0, 0)

    const channelIndex = comp.type === 'capacitor' ? 1 : comp.type === 'terminal' ? 2 : 3
    store.addSortedComponent(comp.type, { x: channelX, y: 0.3, z: -7 }, channelIndex)

    components3D.delete(comp.id)
    store.removeConveyorComponent(comp.id)
    store.setSorting(null)
    activeSortingComponent = null

    roboticArm.position.x = 0
    const gripper = roboticArm.children[0].children.find(c => c.userData.isGripper)
    if (gripper) {
      gripper.position.x = 1.3
      gripper.position.y = 2.7
    }

    // Create a new mesh for retrieval animation
    const retrievedMesh = createComponent3D(comp.type)
    retrievedMesh.position.set(channelX, 0.3, -7)
    scene.add(retrievedMesh)
    
    activeRetrievingMesh = retrievedMesh
    retrievalTargetZ = -10

    animationPhase = 'retrieval'
    currentPhaseTime = 0
  }
}

let activeRetrievingMesh: THREE.Group | null = null
let retrievalTargetZ = -10

function updateRetrievalPhase(delta: number) {
  if (!activeRetrievingMesh) {
    animationPhase = 'idle'
    currentPhaseTime = 0
    return
  }

  const speed = 4 * delta
  if (activeRetrievingMesh.position.z > retrievalTargetZ) {
    activeRetrievingMesh.position.z -= speed
    activeRetrievingMesh.position.y -= speed * 0.5
  }

  if (currentPhaseTime > 1.5) {
    if (activeRetrievingMesh) {
      scene.remove(activeRetrievingMesh)
      activeRetrievingMesh = null
    }
    animationPhase = 'idle'
    currentPhaseTime = 0
  }
}

function updateRoboticArmAnimation() {
  if (store.animationState === 'running' && animationPhase === 'sorting') {
    const comp = activeSortingComponent
    if (comp) {
      roboticArm.rotation.y = Math.sin(clock.getElapsedTime() * 2) * 0.05
    }
  }
}

function spawnComponent(type: ComponentType, id: number) {
  const comp3D = createComponent3D(type)
  comp3D.position.set(-15, 0.5, 0)
  comp3D.castShadow = true
  comp3D.userData.id = id
  components3D.set(id, comp3D)
  conveyorItems.add(comp3D)
}

watch(() => store.conveyorComponents.length, (newLen, oldLen) => {
  if (newLen > oldLen) {
    const newComp = store.conveyorComponents[newLen - 1]
    spawnComponent(newComp.type, newComp.id)
  }
})

watch(() => store.animationState, (newState) => {
  if (newState === 'stopped') {
    animationPhase = 'idle'
    currentPhaseTime = 0
    components3D.forEach((obj) => {
      conveyorItems.remove(obj)
    })
    components3D.clear()
    roboticArm.position.x = 0
    const gripper = roboticArm.children[0]?.children?.find(c => c.userData.isGripper)
    if (gripper) {
      gripper.position.x = 1.3
      gripper.position.y = 2.7
    }
    retrievedComponents = []
  }
})

onMounted(() => {
  initScene()
  animate()
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
  cancelAnimationFrame(animationId)
  renderer?.dispose()
})
</script>

<template>
  <div ref="containerRef" class="three-container"></div>
</template>

<style scoped>
.three-container {
  width: 100%;
  height: 100%;
}
</style>
