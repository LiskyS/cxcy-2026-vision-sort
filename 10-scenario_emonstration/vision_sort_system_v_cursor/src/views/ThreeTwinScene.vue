<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { PartType } from '../sim/twinTypes'
import { clamp, easeInOutCubic, lerp, vec3 } from '../sim/utils'
import { useTwinStore } from '../sim/twinStore'

type PartStage = 'feed' | 'recognize' | 'toSort' | 'waitingPick' | 'picked' | 'toChannel' | 'toBox'

type SimPart = {
  id: number
  type: PartType
  stage: PartStage
  mesh: THREE.Object3D
  pos: THREE.Vector3
  t: number
  recognized: boolean
  recogEnqueued: boolean
}

type RobotPhase =
  | 'idle'
  | 'moveAbovePick'
  | 'lowerPick'
  | 'liftPick'
  | 'moveAboveDrop'
  | 'lowerDrop'
  | 'liftAfterDrop'

const wrapEl = ref<HTMLDivElement | null>(null)
const store = useTwinStore()

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let raf = 0

let lastFrameMs = 0
let parts: SimPart[] = []
let nextId = 1

type RecogJob = {
  partId: number
  type: PartType
  snap: { x: number; y: number; z: number }
  remainingS: number
}

// recognition is modeled as an async pipeline with limited concurrency
const RECOG_WORKERS = 2
const RECOG_LATENCY_S = 0.32
const RECOG_QUEUE_MAX = 10
const PICK_QUEUE_MAX = 8
let recogQueue: RecogJob[] = []
let recogActive: RecogJob[] = []

// ---------- Layout constants (world coords) ----------
const FEED_X0 = -8
const RECOG_X = -2.2
const SORT_X = 2.2
const DROP_X = 4.8
const EXIT_X = 8.0

const CONVEYOR_Y = 0.25
// push robot frame backward so it won't block channel view
const ROBOT_ROOT_Z = -4.2
// pick station (parts will decelerate and stop here)
const PICK_X = SORT_X - 0.12
const PICK_ZONE_HALF = 0.55
// upstream buffer so sorting area doesn't pile up
const PICK_BUFFER_X = PICK_X - 1.35
const PICK_QUEUE_SPACING = 0.42
// keep parts evenly spaced on main conveyor (prevents recognition-area clustering)
const MAIN_SPACING_X = 0.62

const ROBOT_PHASE_DUR: Record<RobotPhase, number> = {
  idle: 0,
  moveAbovePick: 0.42,
  lowerPick: 0.26,
  liftPick: 0.26,
  moveAboveDrop: 0.48,
  lowerDrop: 0.26,
  liftAfterDrop: 0.24,
}

const ROBOT_CYCLE_BASE_S =
  ROBOT_PHASE_DUR.moveAbovePick +
  ROBOT_PHASE_DUR.lowerPick +
  ROBOT_PHASE_DUR.liftPick +
  ROBOT_PHASE_DUR.moveAboveDrop +
  ROBOT_PHASE_DUR.lowerDrop +
  ROBOT_PHASE_DUR.liftAfterDrop

const channelZ: Record<PartType, number> = {
  电容: -2.6,
  端子: 0,
  连接器: 2.6,
}

// ---------- Visual helper objects ----------
let recogRing: THREE.Mesh | null = null
let cameraBody: THREE.Group | null = null
let cameraSpot: THREE.SpotLight | null = null
let cameraCone: THREE.Mesh | null = null

// ---------- Robot (gantry) ----------
let robot: {
  root: THREE.Group
  carriage: THREE.Group
  vertical: THREE.Mesh
  gripper: THREE.Group
  fingers: [THREE.Mesh, THREE.Mesh]
  phase: RobotPhase
  phaseT: number
  pickPartId: number | null
  targetType: PartType | null
  x: number
  z: number
  y: number
} | null = null

function pickRandomType(): PartType {
  const r = Math.random()
  if (r < 0.34) return '电容'
  if (r < 0.67) return '端子'
  return '连接器'
}

function createPartMesh(type: PartType) {
  const g = new THREE.Group()
  const colors: Record<PartType, number> = {
    电容: 0x2563eb,
    端子: 0xf59e0b,
    连接器: 0x10b981,
  }

  const baseMat = new THREE.MeshStandardMaterial({
    color: colors[type],
    roughness: 0.4,
    metalness: 0.2,
  })

  let body: THREE.Mesh
  if (type === '电容') {
    body = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.35, 20), baseMat)
    body.rotation.z = Math.PI / 2
  } else if (type === '端子') {
    body = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.18, 0.22), baseMat)
  } else {
    body = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.22, 0.32), baseMat)
  }
  body.castShadow = true
  body.receiveShadow = true
  g.add(body)

  // little white label
  const label = new THREE.Mesh(
    new THREE.PlaneGeometry(0.22, 0.12),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 }),
  )
  label.position.set(0, 0.18, 0)
  label.rotation.x = -Math.PI / 2
  g.add(label)

  return g
}

function createFactoryScene() {
  const s = new THREE.Scene()
  s.background = new THREE.Color(0xf4f7ff)

  const hemi = new THREE.HemisphereLight(0xffffff, 0x64748b, 0.85)
  s.add(hemi)

  const dir = new THREE.DirectionalLight(0xffffff, 1.05)
  dir.position.set(-6, 10, 8)
  dir.castShadow = true
  dir.shadow.mapSize.set(2048, 2048)
  dir.shadow.camera.near = 1
  dir.shadow.camera.far = 40
  dir.shadow.camera.left = -15
  dir.shadow.camera.right = 15
  dir.shadow.camera.top = 15
  dir.shadow.camera.bottom = -15
  s.add(dir)

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(60, 30),
    new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.95, metalness: 0 }),
  )
  floor.rotation.x = -Math.PI / 2
  floor.receiveShadow = true
  s.add(floor)

  // safety fence feel (yellow rails)
  const fenceMat = new THREE.MeshStandardMaterial({ color: 0xfbbf24, roughness: 0.6, metalness: 0.05 })
  const fence = new THREE.Group()
  const rail1 = new THREE.Mesh(new THREE.BoxGeometry(16, 0.08, 0.08), fenceMat)
  // move rails outward so they don't visually block output channels
  rail1.position.set(0.2, 0.55, 5.4)
  fence.add(rail1)
  const rail2 = rail1.clone()
  rail2.position.z = -5.4
  fence.add(rail2)
  fence.children.forEach((m: THREE.Object3D) => ((m as THREE.Mesh).castShadow = true))
  s.add(fence)

  // conveyor line
  const conveyor = new THREE.Group()
  const beltMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.6, metalness: 0.2 })
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.5, metalness: 0.3 })

  const belt = new THREE.Mesh(new THREE.BoxGeometry(16, 0.12, 1.3), beltMat)
  belt.position.set((FEED_X0 + EXIT_X) / 2, CONVEYOR_Y, 0)
  belt.castShadow = true
  belt.receiveShadow = true
  conveyor.add(belt)

  const frameL = new THREE.Mesh(new THREE.BoxGeometry(16.2, 0.12, 0.1), frameMat)
  frameL.position.set(belt.position.x, CONVEYOR_Y + 0.1, 0.75)
  frameL.castShadow = true
  frameL.receiveShadow = true
  conveyor.add(frameL)
  const frameR = frameL.clone()
  frameR.position.z = -0.75
  conveyor.add(frameR)

  // legs
  for (let i = 0; i < 7; i++) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.6, 0.08), frameMat)
    leg.position.set(FEED_X0 + 2.2 + i * 2.2, 0.3, 0.62)
    leg.castShadow = true
    conveyor.add(leg)
    const leg2 = leg.clone()
    leg2.position.z = -0.62
    conveyor.add(leg2)
  }
  s.add(conveyor)

  // recognition camera
  cameraBody = new THREE.Group()
  const camHead = new THREE.Mesh(
    new THREE.BoxGeometry(0.55, 0.28, 0.28),
    new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.35, metalness: 0.35 }),
  )
  camHead.position.set(RECOG_X, 2.15, 0)
  camHead.castShadow = true
  cameraBody.add(camHead)
  const camLens = new THREE.Mesh(
    new THREE.CylinderGeometry(0.09, 0.09, 0.2, 20),
    new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.2, metalness: 0.6 }),
  )
  camLens.rotation.z = Math.PI / 2
  camLens.position.set(RECOG_X + 0.35, 2.15, 0)
  camLens.castShadow = true
  cameraBody.add(camLens)
  const camArm = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.05, 2.2, 16),
    new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.6, metalness: 0.25 }),
  )
  camArm.position.set(RECOG_X, 1.05, 0)
  camArm.castShadow = true
  cameraBody.add(camArm)
  s.add(cameraBody)

  // camera light effect: spotlight + translucent cone
  cameraSpot = new THREE.SpotLight(0x22c55e, 0, 4.2, Math.PI * 0.18, 0.55, 1.3)
  cameraSpot.position.set(RECOG_X + 0.45, 2.15, 0)
  cameraSpot.target.position.set(RECOG_X, CONVEYOR_Y + 0.06, 0)
  cameraSpot.castShadow = false
  s.add(cameraSpot)
  s.add(cameraSpot.target)

  cameraCone = new THREE.Mesh(
    new THREE.CylinderGeometry(0.02, 0.58, 1.95, 28, 1, true),
    new THREE.MeshBasicMaterial({
      color: 0x22c55e,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  )
  cameraCone.position.set(RECOG_X + 0.25, 1.18, 0)
  cameraCone.renderOrder = 10
  s.add(cameraCone)

  // recognition ring (projected light)
  recogRing = new THREE.Mesh(
    new THREE.RingGeometry(0.18, 0.32, 42),
    new THREE.MeshBasicMaterial({ color: 0x22c55e, transparent: true, opacity: 0.0, side: THREE.DoubleSide }),
  )
  recogRing.rotation.x = -Math.PI / 2
  recogRing.position.set(RECOG_X, CONVEYOR_Y + 0.07, 0)
  s.add(recogRing)

  // output channels and boxes
  const channelMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.55, metalness: 0.25 })
  const boxMat = new THREE.MeshStandardMaterial({ color: 0xe0f2fe, roughness: 0.85, metalness: 0.05 })

  ;(['电容', '端子', '连接器'] as PartType[]).forEach((t) => {
    const z = channelZ[t]
    const channel = new THREE.Mesh(new THREE.BoxGeometry(6.3, 0.1, 0.9), channelMat)
    channel.position.set((DROP_X + EXIT_X) / 2, CONVEYOR_Y, z)
    channel.castShadow = true
    channel.receiveShadow = true
    s.add(channel)

    const box = new THREE.Mesh(new THREE.BoxGeometry(1.15, 0.65, 1.0), boxMat)
    box.position.set(EXIT_X + 1.0, 0.32, z)
    box.castShadow = true
    box.receiveShadow = true
    s.add(box)

    const boxEdge = new THREE.Mesh(
      new THREE.BoxGeometry(1.18, 0.68, 1.03),
      new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.6, metalness: 0.15, transparent: true, opacity: 0.35 }),
    )
    boxEdge.position.copy(box.position)
    boxEdge.castShadow = false
    boxEdge.receiveShadow = true
    s.add(boxEdge)
  })

  // pick station stopper / platform (helps logic: part定位、机械臂抓取)
  const pickPlate = new THREE.Mesh(
    new THREE.BoxGeometry(1.25, 0.08, 1.55),
    new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.65, metalness: 0.2 }),
  )
  pickPlate.position.set(PICK_X, CONVEYOR_Y + 0.02, 0)
  pickPlate.castShadow = true
  pickPlate.receiveShadow = true
  s.add(pickPlate)

  // robot (gantry)
  robot = createRobot()
  s.add(robot.root)

  return s
}

function createRobot() {
  const root = new THREE.Group()
  root.position.set(SORT_X, 0, ROBOT_ROOT_Z)

  const frameMat = new THREE.MeshStandardMaterial({ color: 0x0ea5e9, roughness: 0.45, metalness: 0.25 })
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.55, metalness: 0.35 })

  // ground base + rails (avoid “悬空” perception)
  const baseMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.65, metalness: 0.25 })
  const base = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.12, 2.2), baseMat)
  base.position.set(1.0, 0.06, 0.0)
  base.castShadow = true
  base.receiveShadow = true
  root.add(base)

  const railL = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.10, 0.12), baseMat)
  railL.position.set(1.0, 0.12, 0.95)
  railL.castShadow = true
  root.add(railL)
  const railR = railL.clone()
  railR.position.z = -0.95
  root.add(railR)

  const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.5, 2.6, 0.5), frameMat)
  pillar.position.set(0, 1.3, 0)
  pillar.castShadow = true
  root.add(pillar)

  const beam = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.22, 0.5), frameMat)
  beam.position.set(0.9, 2.45, 0)
  beam.castShadow = true
  root.add(beam)

  const carriage = new THREE.Group()
  carriage.position.set(0.0, 2.45, 0)
  root.add(carriage)

  const carBody = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.25, 0.55), darkMat)
  carBody.position.set(0.9, 0, 0)
  carBody.castShadow = true
  carriage.add(carBody)

  const vertical = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.3, 16), darkMat)
  vertical.position.set(0.9, -0.65, 0)
  vertical.castShadow = true
  carriage.add(vertical)

  const gripper = new THREE.Group()
  gripper.position.set(0.9, -1.3, 0)
  carriage.add(gripper)

  const fingerMat = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.4, metalness: 0.35 })
  const f1 = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.25, 0.07), fingerMat)
  f1.position.set(0.12, -0.12, 0.07)
  f1.castShadow = true
  const f2 = f1.clone()
  f2.position.z = -0.07
  gripper.add(f1, f2)

  return {
    root,
    carriage,
    vertical,
    gripper,
    fingers: [f1, f2] as [THREE.Mesh, THREE.Mesh],
    phase: 'idle' as RobotPhase,
    phaseT: 0,
    pickPartId: null as number | null,
    targetType: null as PartType | null,
    x: SORT_X,
    z: 0,
    y: 2.45,
  }
}

function resetSim() {
  // remove parts
  if (scene) {
    for (const p of parts) scene.remove(p.mesh)
  }
  parts = []
  nextId = 1
  recogQueue = []
  recogActive = []

  if (robot) {
    robot.phase = 'idle'
    robot.phaseT = 0
    robot.pickPartId = null
    robot.targetType = null
    robot.carriage.position.set(0, 2.45, 0)
    robot.vertical.scale.set(1, 1, 1)
    robot.gripper.position.set(0.9, -1.3, 0)
  }
}

function ensurePartSpawn(dt: number) {
  // spawn density depends on speed and current count
  const maxInLine = 10
  if (parts.length >= maxInLine) return

  // backpressure: if recognition/sort queues are full, slow/stop feeding
  const qPick = parts.filter((p) => p.stage === 'waitingPick' || p.stage === 'picked').length
  const qRecog = recogQueue.length + recogActive.length
  store.setQueues(qRecog, qPick)
  if (qRecog >= RECOG_QUEUE_MAX || qPick >= PICK_QUEUE_MAX) {
    store.markFeedBlocked()
    return
  }

  store.state.tick += dt
  // line takt time: match feed with recognition + robot throughput (slowest stage dominates)
  const recogService = RECOG_LATENCY_S / Math.max(1, RECOG_WORKERS)
  const taktBase = Math.max(ROBOT_CYCLE_BASE_S, recogService) * 1.05
  // if queues start to build, add extra spacing to keep things stable
  const pressure = clamp(qRecog / RECOG_QUEUE_MAX + qPick / PICK_QUEUE_MAX, 0, 2)
  const interval = (taktBase * (1 + pressure * 0.35)) / store.state.speed
  if (store.state.tick < interval) return
  // also enforce a minimum spacing at the belt entrance so parts won't “扎堆”
  const nearestToFeed = parts
    .filter((p) => p.stage === 'feed' || p.stage === 'recognize' || p.stage === 'toSort')
    .reduce<number | null>((minX, p) => (minX === null ? p.mesh.position.x : Math.min(minX, p.mesh.position.x)), null)
  if (nearestToFeed !== null && nearestToFeed < FEED_X0 + MAIN_SPACING_X) return

  store.state.tick = 0

  const type = pickRandomType()
  const mesh = createPartMesh(type)
  mesh.position.set(FEED_X0, CONVEYOR_Y + 0.18, (Math.random() - 0.5) * 0.55)
  if (scene) scene.add(mesh)
  store.markFeedSpawned()
  parts.push({
    id: nextId++,
    type,
    stage: 'feed',
    mesh,
    pos: mesh.position.clone(),
    t: 0,
    recognized: false,
    recogEnqueued: false,
  })
}

function stepRecognition(dt: number) {
  // update queue stats for UI
  const qPick = parts.filter((p) => p.stage === 'waitingPick' || p.stage === 'picked').length
  store.setQueues(recogQueue.length + recogActive.length, qPick)

  // pull new jobs into active pool
  while (recogActive.length < RECOG_WORKERS && recogQueue.length > 0) {
    const j = recogQueue.shift()!
    j.remainingS = RECOG_LATENCY_S
    recogActive.push(j)
  }

  const dtSim = dt * store.state.speed
  for (let i = recogActive.length - 1; i >= 0; i--) {
    const job = recogActive[i]
    job.remainingS -= dtSim
    if (job.remainingS > 0) continue

    const part = parts.find((p) => p.id === job.partId)
    if (part && !part.recognized) {
      part.recognized = true
      // recognition result uses live position for better coherence
      store.markRecognized(part.type, vec3(part.mesh.position.x, part.mesh.position.y, part.mesh.position.z))
    }
    recogActive.splice(i, 1)
  }
}

function updateRecognitionFx(dt: number) {
  if (!recogRing || !cameraBody) return
  const mat = recogRing.material as THREE.MeshBasicMaterial
  const isActive = parts.some((p) => Math.abs(p.mesh.position.x - RECOG_X) < 0.25 && !p.recognized)
  const target = isActive ? 0.9 : 0.0
  mat.opacity = lerp(mat.opacity, target, clamp(dt * 7, 0, 1))

  // ring breathing + scan glow
  const t = performance.now() * 0.001
  const pulse = 0.55 + 0.45 * Math.sin(t * 6.2)
  const targetScale = isActive ? 1 + pulse * 0.18 : 1
  recogRing.scale.x = lerp(recogRing.scale.x, targetScale, clamp(dt * 8, 0, 1))
  recogRing.scale.z = recogRing.scale.x

  if (cameraSpot) {
    const intensityTarget = isActive ? 2.1 + pulse * 0.8 : 0
    cameraSpot.intensity = lerp(cameraSpot.intensity, intensityTarget, clamp(dt * 7, 0, 1))
  }
  if (cameraCone) {
    const coneMat = cameraCone.material as THREE.MeshBasicMaterial
    const coneTarget = isActive ? 0.18 + pulse * 0.08 : 0
    coneMat.opacity = lerp(coneMat.opacity, coneTarget, clamp(dt * 7, 0, 1))
  }

  // camera micro motion
  cameraBody.position.y = Math.sin(t * 2.2) * 0.02
}

function updateParts(dt: number) {
  const v = 1.25 * store.state.speed
  const dropY = CONVEYOR_Y + 0.18

  const sortingBusy =
    (robot?.phase ?? 'idle') !== 'idle' ||
    parts.some((p) => p.stage === 'waitingPick' || p.stage === 'picked')
  const queueCandidates = parts
    .filter((p) => p.stage === 'feed' || p.stage === 'recognize' || p.stage === 'toSort')
    .filter((p) => p.recognized)
    .sort((a, b) => a.mesh.position.x - b.mesh.position.x)

  for (const p of parts) {
    if (p.stage === 'picked') continue

    if (p.stage === 'feed' || p.stage === 'recognize' || p.stage === 'toSort') {
      // feed/recognize/toSort: move on main conveyor (recognition does NOT stop parts)
      // only in pick zone (after recognition) we decelerate for better robot pick logic
      const inPickZone = p.recognized && p.mesh.position.x >= PICK_X - PICK_ZONE_HALF
      const vNow = inPickZone ? v * 0.45 : v

      // if robot is busy, keep recognized parts in an upstream queue (do not pile up at sorting area)
      if (p.recognized && sortingBusy) {
        const idx = queueCandidates.findIndex((q) => q.id === p.id)
        const targetX = PICK_BUFFER_X - Math.max(0, idx) * PICK_QUEUE_SPACING
        if (p.mesh.position.x >= targetX) {
          p.mesh.position.x = targetX
        } else {
          p.mesh.position.x += vNow * dt
        }
      } else {
        p.mesh.position.x += vNow * dt
      }
      p.mesh.position.y = dropY
      p.mesh.rotation.y += dt * 1.5

      // enqueue recognition once when entering recognition window; result will be produced later
      if (!p.recognized && !p.recogEnqueued && p.mesh.position.x >= RECOG_X - 0.12) {
        p.stage = 'recognize'
        p.recogEnqueued = true
        if (recogQueue.length < RECOG_QUEUE_MAX) {
          store.markRecogQueued()
          recogQueue.push({
            partId: p.id,
            type: p.type,
            snap: { x: p.mesh.position.x, y: p.mesh.position.y, z: p.mesh.position.z },
            remainingS: RECOG_LATENCY_S,
          })
        } else {
          // queue overflow: treat as blocked feed signal (keeps system stable)
          store.markFeedBlocked()
        }
      }

      // only allow one part to enter pick station at a time
      if (!sortingBusy && p.recognized && p.mesh.position.x >= PICK_X) {
        // stopper定位：等待机械臂根据识别结果分拣
        p.mesh.position.x = PICK_X
        p.stage = 'waitingPick'
      } else if (p.mesh.position.x >= RECOG_X + 0.4) {
        p.stage = 'toSort'
      }
    } else if (p.stage === 'waitingPick') {
      // keep still on pick station until robot picks it
      p.mesh.position.x = PICK_X
      p.mesh.position.y = dropY
    } else if (p.stage === 'toChannel') {
      // after drop, move along channel to exit
      const zt = channelZ[p.type]
      p.mesh.position.z = lerp(p.mesh.position.z, zt, clamp(dt * 4, 0, 1))
      p.mesh.position.x += v * dt
      if (p.mesh.position.x >= EXIT_X) {
        p.stage = 'toBox'
        p.t = 0
      }
    } else if (p.stage === 'toBox') {
      p.t += dt * store.state.speed
      const t = clamp(p.t / 0.6, 0, 1)
      const e = easeInOutCubic(t)
      p.mesh.position.y = lerp(dropY, 0.05, e)
      p.mesh.position.x = lerp(EXIT_X, EXIT_X + 0.85, e)
      if (t >= 1) {
        store.markSorted(p.type, vec3(p.mesh.position.x, p.mesh.position.y, p.mesh.position.z))
        if (scene) scene.remove(p.mesh)
        p.stage = 'feed' // mark as removable
      }
    }
    store.updateLastKnown(vec3(p.mesh.position.x, p.mesh.position.y, p.mesh.position.z))
  }

  // enforce spacing on main conveyor so parts won't cluster at recognition
  const mainBelt = parts
    .filter((p) => p.stage === 'feed' || p.stage === 'recognize' || p.stage === 'toSort')
    .sort((a, b) => b.mesh.position.x - a.mesh.position.x) // front -> back
  for (let i = 1; i < mainBelt.length; i++) {
    const front = mainBelt[i - 1]
    const back = mainBelt[i]
    const limitX = front.mesh.position.x - MAIN_SPACING_X
    if (back.mesh.position.x > limitX) back.mesh.position.x = limitX
  }

  // remove delivered parts
  parts = parts.filter((p) => !(p.recognized && p.stage === 'feed' && p.mesh.parent === null))
}

function stepRobot(dt: number) {
  if (!robot || !scene) return
  const rb = robot

  // acquire a part waiting for pick near sort x
  if (rb.phase === 'idle') {
    const candidate = parts
      .filter((p) => p.stage === 'waitingPick')
      .sort((a, b) => a.mesh.position.x - b.mesh.position.x)[0]
    if (!candidate) return

    rb.pickPartId = candidate.id
    rb.targetType = candidate.type
    rb.phase = 'moveAbovePick'
    rb.phaseT = 0
    store.markSortPicked()
  }

  const part = rb.pickPartId ? parts.find((p) => p.id === rb.pickPartId) : undefined
  if (!part) {
    rb.phase = 'idle'
    rb.pickPartId = null
    rb.targetType = null
    return
  }

  const pickPos = new THREE.Vector3(PICK_X, CONVEYOR_Y + 0.18, part.mesh.position.z)
  const dropPos = new THREE.Vector3(DROP_X, CONVEYOR_Y + 0.18, channelZ[part.type])

  const carriageWorldX = (x: number) => x - SORT_X + 0.0 // root is at SORT_X
  const carriageWorldZ = (z: number) => z - ROBOT_ROOT_Z // root is offset on Z

  const moveCarriageTo = (x: number, z: number, t01: number) => {
    const e = easeInOutCubic(t01)
    rb.carriage.position.x = lerp(rb.carriage.position.x, carriageWorldX(x), clamp(e * 1.2, 0, 1))
    rb.carriage.position.z = lerp(rb.carriage.position.z, carriageWorldZ(z), clamp(e * 1.2, 0, 1))
  }

  const setLift = (down01: number) => {
    // scale the vertical rod and move gripper
    const down = clamp(down01, 0, 1)
    rb.vertical.scale.y = 1 + down * 0.85
    rb.gripper.position.y = -1.3 - down * 1.1
  }

  const closeFingers = (close01: number) => {
    const c = clamp(close01, 0, 1)
    rb.fingers[0].position.x = lerp(0.12, 0.06, c)
    rb.fingers[1].position.x = lerp(0.12, 0.06, c)
  }

  const speed = 1.0 * store.state.speed
  const phaseDur = ROBOT_PHASE_DUR

  const advance = () => {
    robot!.phaseT = 0
    if (robot!.phase === 'moveAbovePick') robot!.phase = 'lowerPick'
    else if (robot!.phase === 'lowerPick') robot!.phase = 'liftPick'
    else if (robot!.phase === 'liftPick') robot!.phase = 'moveAboveDrop'
    else if (robot!.phase === 'moveAboveDrop') robot!.phase = 'lowerDrop'
    else if (robot!.phase === 'lowerDrop') robot!.phase = 'liftAfterDrop'
    else if (robot!.phase === 'liftAfterDrop') {
      robot!.phase = 'idle'
      robot!.pickPartId = null
      robot!.targetType = null
    }
  }

  const dur = phaseDur[rb.phase]
  rb.phaseT += dt * speed
  const t01 = dur <= 0 ? 1 : clamp(rb.phaseT / dur, 0, 1)

  if (rb.phase === 'moveAbovePick') {
    moveCarriageTo(pickPos.x, pickPos.z, t01)
    setLift(0)
    closeFingers(0)
  } else if (rb.phase === 'lowerPick') {
    moveCarriageTo(pickPos.x, pickPos.z, 1)
    setLift(t01)
    closeFingers(t01 * 0.75)
    if (t01 > 0.7) part.stage = 'picked'
  } else if (rb.phase === 'liftPick') {
    moveCarriageTo(pickPos.x, pickPos.z, 1)
    setLift(1 - t01)
    closeFingers(0.75)
  } else if (rb.phase === 'moveAboveDrop') {
    moveCarriageTo(dropPos.x, dropPos.z, t01)
    setLift(0)
    closeFingers(0.75)
  } else if (rb.phase === 'lowerDrop') {
    moveCarriageTo(dropPos.x, dropPos.z, 1)
    setLift(t01)
    closeFingers(0.75 - t01 * 0.75)
    if (t01 > 0.75) {
      // release
      part.stage = 'toChannel'
      part.mesh.position.set(dropPos.x, dropPos.y, dropPos.z)
    }
  } else if (rb.phase === 'liftAfterDrop') {
    moveCarriageTo(dropPos.x, dropPos.z, 1)
    setLift(1 - t01)
    closeFingers(0)
  }

  // attach picked part to gripper
  if (part.stage === 'picked') {
    const gp = new THREE.Vector3()
    rb.gripper.getWorldPosition(gp)
    part.mesh.position.copy(gp)
    part.mesh.position.y -= 0.12
  }

  if (t01 >= 1) advance()
}

function animate() {
  if (!renderer || !scene || !camera) return
  raf = requestAnimationFrame(animate)

  const now = performance.now()
  const dtRaw = lastFrameMs ? (now - lastFrameMs) / 1000 : 1 / 60
  lastFrameMs = now
  const dt = Math.min(dtRaw, 0.033)

  if (store.state.status === 'running') {
    ensurePartSpawn(dt)
    stepRecognition(dt)
    updateRecognitionFx(dt)
    updateParts(dt)
    stepRobot(dt)
  } else {
    updateRecognitionFx(dt)
  }

  controls?.update()
  renderer.render(scene, camera)
}

function resize() {
  if (!renderer || !camera || !wrapEl.value) return
  const w = wrapEl.value.clientWidth
  const h = wrapEl.value.clientHeight
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

onMounted(() => {
  if (!wrapEl.value) return

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  wrapEl.value.appendChild(renderer.domElement)

  scene = createFactoryScene()
  camera = new THREE.PerspectiveCamera(48, 1, 0.1, 120)
  // slightly adjust angle to keep channels visible
  camera.position.set(-6.2, 7.2, 10.8)
  camera.lookAt(new THREE.Vector3(2.2, 1.0, 0))

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.enableRotate = true
  controls.enableZoom = true
  controls.enablePan = true
  controls.target.set(2.2, 1.0, 0)
  controls.minDistance = 5
  controls.maxDistance = 30
  controls.maxPolarAngle = Math.PI * 0.49
  controls.update()

  resize()
  window.addEventListener('resize', resize)

  lastFrameMs = performance.now()
  animate()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  cancelAnimationFrame(raf)
  controls?.dispose()
  controls = null
  if (renderer) {
    renderer.dispose()
    renderer = null
  }
  scene = null
  camera = null
})

watch(
  () => store.state.status,
  (s) => {
    if (s === 'stopped') resetSim()
    if (s === 'paused') {
      lastFrameMs = performance.now()
    }
    if (s === 'running') {
      lastFrameMs = performance.now()
    }
  },
)
</script>

<template>
  <div ref="wrapEl" style="position: absolute; inset: 0" />
</template>

