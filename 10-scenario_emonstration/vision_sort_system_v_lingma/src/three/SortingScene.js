import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import RoboticArmController from './controllers/RoboticArmController'

class SortingScene {
  constructor(container, store) {
    this.container = container
    this.store = store
    this.scene = null 
    this.camera = null
    this.renderer = null
    this.controls = null
    this.clock = new THREE.Clock()
    
    // Scene objects
    this.conveyorBelt = null
    this.camera3D = null
    this.roboticHand = null
    this.gripperTip = null
    this.gripperFingers = null
    this.armController = null
    this.armSignals = { phase: 'idle', shouldAttach: false, shouldRelease: false }
    this.outputChannels = []
    this.trucks = []
    this.components = []
    
    // Animation state
    this.isRunning = false
    this.isPaused = false
    this.animationPhase = 'idle'
    this.componentSpawnTimer = 0
    this.componentSpawnInterval = 0.8 // seconds
    
    // Component types
    this.componentTypes = ['capacitor', 'terminal', 'connector']
  }

  init() {
    this.createScene()
    this.createCamera()
    this.createRenderer()
    this.createLights()
    this.createEnvironment()
    this.createConveyorBelt()
    this.createIdentificationCamera()
    this.createRoboticArm()
    this.createControllers()
    this.createOutputChannels()
    this.createTrucks()
    this.setupControls()
    this.animate()
  }

  createScene() {
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0xd8dce5)
    this.scene.fog = new THREE.Fog(0xd8dce5, 50, 100)
  }

  createCamera() {
    this.camera = new THREE.PerspectiveCamera(
      60,
      this.container.clientWidth / this.container.clientHeight,
      0.1,
      1000
    )
    this.camera.position.set(20, 15, 20)
    this.camera.lookAt(0, 0, 0)
  }

  createRenderer() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight)
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap
    this.container.appendChild(this.renderer.domElement)
  }

  createLights() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    this.scene.add(ambientLight)

    // Directional light (sun)
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
    dirLight.position.set(20, 30, 20)
    dirLight.castShadow = true
    dirLight.shadow.mapSize.width = 2048
    dirLight.shadow.mapSize.height = 2048
    dirLight.shadow.camera.near = 0.5
    dirLight.shadow.camera.far = 100
    dirLight.shadow.camera.left = -30
    dirLight.shadow.camera.right = 30
    dirLight.shadow.camera.top = 30
    dirLight.shadow.camera.bottom = -30
    this.scene.add(dirLight)

    // Point lights for better illumination
    const pointLight1 = new THREE.PointLight(0x409eff, 0.5, 50)
    pointLight1.position.set(-10, 10, 0)
    this.scene.add(pointLight1)

    const pointLight2 = new THREE.PointLight(0x67c23a, 0.5, 50)
    pointLight2.position.set(10, 10, 0)
    this.scene.add(pointLight2)
  }

  createEnvironment() {
    // Floor - industrial polished concrete
    const floorGeometry = new THREE.PlaneGeometry(100, 100)
    const floorMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xe8eaed,
      roughness: 0.3,
      metalness: 0.1
    })
    const floor = new THREE.Mesh(floorGeometry, floorMaterial)
    floor.rotation.x = -Math.PI / 2
    floor.receiveShadow = true
    this.scene.add(floor)

    // Grid helper - subtle industrial grid
    const gridHelper = new THREE.GridHelper(100, 50, 0xc0c4cc, 0xd5d8de)
    this.scene.add(gridHelper)
  }

  createConveyorBelt() {
    // Main conveyor belt - industrial black belt
    const beltGeometry = new THREE.BoxGeometry(30, 0.5, 3)
    const beltMaterial = new THREE.MeshStandardMaterial({ 
      color: 0x1a1a1a,
      roughness: 0.7,
      metalness: 0.1
    })
    this.conveyorBelt = new THREE.Mesh(beltGeometry, beltMaterial)
    this.conveyorBelt.position.set(-5, 0.25, 0)
    this.conveyorBelt.receiveShadow = true
    this.conveyorBelt.castShadow = true
    this.scene.add(this.conveyorBelt)

    // Conveyor frame - aluminum profile (silver)
    const frameMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xc0c4cc,
      roughness: 0.4,
      metalness: 0.7
    })

    // Left side frame
    const leftFrame = new THREE.Mesh(new THREE.BoxGeometry(30, 1, 0.2), frameMaterial)
    leftFrame.position.set(-5, 0.75, -1.6)
    leftFrame.castShadow = true
    this.scene.add(leftFrame)

    // Right side frame
    const rightFrame = new THREE.Mesh(new THREE.BoxGeometry(30, 1, 0.2), frameMaterial)
    rightFrame.position.set(-5, 0.75, 1.6)
    rightFrame.castShadow = true
    this.scene.add(rightFrame)

    // Support legs - aluminum profile
    for (let x = -18; x <= 8; x += 6) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.5, 0.3), frameMaterial)
      leg.position.set(x, 0.75, -1.6)
      leg.castShadow = true
      this.scene.add(leg)

      const leg2 = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.5, 0.3), frameMaterial)
      leg2.position.set(x, 0.75, 1.6)
      leg2.castShadow = true
      this.scene.add(leg2)
    }

    // Yellow safety markers on frame
    const safetyMaterial = new THREE.MeshStandardMaterial({ 
      color: 0xffc107,
      roughness: 0.5,
      metalness: 0.3
    })
    for (let x = -18; x <= 8; x += 12) {
      const marker = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.2, 3.4), safetyMaterial)
      marker.position.set(x, 0.75, 0)
      marker.castShadow = true
      this.scene.add(marker)
    }

    // Moving belt texture effect (lines)
    const lineCount = 20
    for (let i = 0; i < lineCount; i++) {
      const line = new THREE.Mesh(
        new THREE.BoxGeometry(0.1, 0.52, 2.8),
        new THREE.MeshStandardMaterial({ color: 0x2a2a2a })
      )
      line.position.set(-19 + i * 1.5, 0.25, 0)
      line.userData.isBeltLine = true
      line.userData.initialX = -19 + i * 1.5
      this.scene.add(line)
    }
  }

  createIdentificationCamera() {
    // Camera housing
    const housingGeometry = new THREE.BoxGeometry(2, 2.5, 2)
    const housingMaterial = new THREE.MeshStandardMaterial({ 
      color: 0x34495e,
      roughness: 0.4,
      metalness: 0.6
    })
    const housing = new THREE.Mesh(housingGeometry, housingMaterial)
    housing.position.set(0, 4, 0)
    housing.castShadow = true
    this.scene.add(housing)

    // Camera lens
    const lensGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.5, 16)
    const lensMaterial = new THREE.MeshStandardMaterial({ 
      color: 0x1a1a1a,
      roughness: 0.2,
      metalness: 0.8
    })
    const lens = new THREE.Mesh(lensGeometry, lensMaterial)
    lens.rotation.x = Math.PI / 2
    lens.position.set(0, 2.5, 0)
    this.scene.add(lens)

    // Camera stand
    const standGeometry = new THREE.CylinderGeometry(0.2, 0.3, 3, 8)
    const standMaterial = new THREE.MeshStandardMaterial({ 
      color: 0x7f8c8d,
      roughness: 0.5,
      metalness: 0.5
    })
    const stand = new THREE.Mesh(standGeometry, standMaterial)
    stand.position.set(0, 2.5, -3)
    stand.castShadow = true
    this.scene.add(stand)

    // Scanning light effect - main spotlight
    const scanLight = new THREE.SpotLight(0x409eff, 2, 15, Math.PI / 6, 0.5, 1)
    scanLight.position.set(0, 3.5, 0)
    scanLight.target.position.set(0, 0.5, 0)
    scanLight.castShadow = true
    scanLight.userData.isScanLight = true
    this.scene.add(scanLight)
    this.scene.add(scanLight.target)

    // Scanning beam cone (visual effect)
    const beamGeometry = new THREE.ConeGeometry(1.5, 3, 32, 1, true)
    const beamMaterial = new THREE.MeshBasicMaterial({
      color: 0x409eff,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })
    const scanBeam = new THREE.Mesh(beamGeometry, beamMaterial)
    scanBeam.position.set(0, 2, 0)
    scanBeam.userData.isScanBeam = true
    this.scene.add(scanBeam)

    // Scanning ring effect
    const ringGeometry = new THREE.RingGeometry(0.8, 1, 32)
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x409eff,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })
    const scanRing = new THREE.Mesh(ringGeometry, ringMaterial)
    scanRing.rotation.x = -Math.PI / 2
    scanRing.position.set(0, 0.6, 0)
    scanRing.userData.isScanRing = true
    this.scene.add(scanRing)

    // Additional point lights for better illumination
    const scanPointLight1 = new THREE.PointLight(0x409eff, 1, 8)
    scanPointLight1.position.set(-1, 2.5, 0)
    scanPointLight1.userData.isScanLight = true
    this.scene.add(scanPointLight1)

    const scanPointLight2 = new THREE.PointLight(0x409eff, 1, 8)
    scanPointLight2.position.set(1, 2.5, 0)
    scanPointLight2.userData.isScanLight = true
    this.scene.add(scanPointLight2)

    // Scanning laser line
    const laserGeometry = new THREE.BoxGeometry(2.5, 0.05, 0.05)
    const laserMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
    const scanLaser = new THREE.Mesh(laserGeometry, laserMaterial)
    scanLaser.position.set(0, 0.7, 0)
    scanLaser.visible = false
    scanLaser.userData.isScanLaser = true
    this.scene.add(scanLaser)

    this.camera3D = { housing, lens, scanLight, scanBeam, scanRing, scanPointLight1, scanPointLight2, scanLaser }
  }

  createRoboticArm() {
    // Create only the robotic hand (end-effector) without the arm
    this.roboticHand = new THREE.Group()

    const gripperMaterial = new THREE.MeshStandardMaterial({
      color: 0x2a2a2a,
      roughness: 0.4,
      metalness: 0.6
    })

    // Gripper base
    const gripperBaseGeometry = new THREE.BoxGeometry(0.8, 0.25, 0.4)
    const gripperBase = new THREE.Mesh(gripperBaseGeometry, gripperMaterial)
    gripperBase.castShadow = true
    this.roboticHand.add(gripperBase)

    // Left finger
    const fingerGeometry = new THREE.BoxGeometry(0.15, 0.6, 0.15)
    const leftFinger = new THREE.Mesh(fingerGeometry, gripperMaterial)
    leftFinger.position.set(0, -0.4, -0.15)
    leftFinger.castShadow = true
    leftFinger.userData.isFinger = true
    leftFinger.userData.side = 'left'
    this.roboticHand.add(leftFinger)

    // Right finger
    const rightFinger = new THREE.Mesh(fingerGeometry, gripperMaterial)
    rightFinger.position.set(0, -0.4, 0.15)
    rightFinger.castShadow = true
    rightFinger.userData.isFinger = true
    rightFinger.userData.side = 'right'
    this.roboticHand.add(rightFinger)

    // Gripper tip (attachment point for components)
    this.gripperTip = new THREE.Object3D()
    this.gripperTip.position.set(0, -0.4, 0)
    this.roboticHand.add(this.gripperTip)

    this.gripperFingers = { leftFinger, rightFinger }
    
    // Set armSegments to null since we removed the arm
    this.armSegments = null

    console.log('Robotic hand created (arm removed)')

    // Place the hand at a visible standby position near pickup point.
    this.roboticHand.position.set(4.5, 3.2, 0)
    this.scene.add(this.roboticHand)
  }

  createControllers() {
    if (!this.roboticHand || !this.gripperTip || !this.gripperFingers) return

    this.armController = new RoboticArmController({
      handGroup: this.roboticHand,
      gripperTip: this.gripperTip,
      gripperFingers: this.gripperFingers,
      homePosition: new THREE.Vector3(4.5, 3.2, 0)
    })
  }

  createOutputChannels() {
    const channelPositions = [
      { x: 12, z: -5, color: 0x409eff, name: 'capacitor', label: '电容' },
      { x: 12, z: 0, color: 0x67c23a, name: 'terminal', label: '端子' },
      { x: 12, z: 5, color: 0xe6a23c, name: 'connector', label: '连接器' }
    ]

    channelPositions.forEach((pos, index) => {
      const channel = new THREE.Group()

      // Channel base - industrial bin
      const baseGeometry = new THREE.BoxGeometry(4, 0.3, 2)
      const baseMaterial = new THREE.MeshStandardMaterial({ 
        color: 0xbdc3c7,
        roughness: 0.4,
        metalness: 0.5
      })
      const base = new THREE.Mesh(baseGeometry, baseMaterial)
      base.position.y = 0.15
      base.receiveShadow = true
      channel.add(base)

      // Colored indicator strip
      const stripGeometry = new THREE.BoxGeometry(4, 0.05, 2)
      const stripMaterial = new THREE.MeshStandardMaterial({ 
        color: pos.color,
        roughness: 0.5,
        metalness: 0.3,
        emissive: pos.color,
        emissiveIntensity: 0.2
      })
      const strip = new THREE.Mesh(stripGeometry, stripMaterial)
      strip.position.y = 0.32
      channel.add(strip)

      // Side walls - aluminum profile
      const wallMaterial = new THREE.MeshStandardMaterial({ 
        color: 0xc0c4cc,
        roughness: 0.4,
        metalness: 0.6
      })

      const leftWall = new THREE.Mesh(new THREE.BoxGeometry(4, 0.8, 0.1), wallMaterial)
      leftWall.position.set(0, 0.55, -1)
      leftWall.castShadow = true
      channel.add(leftWall)

      const rightWall = new THREE.Mesh(new THREE.BoxGeometry(4, 0.8, 0.1), wallMaterial)
      rightWall.position.set(0, 0.55, 1)
      rightWall.castShadow = true
      channel.add(rightWall)

      // Back wall
      const backWall = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 2), wallMaterial)
      backWall.position.set(-2, 0.55, 0)
      backWall.castShadow = true
      channel.add(backWall)

      channel.position.set(pos.x, 0, pos.z)
      channel.userData.name = pos.name
      channel.userData.index = index
      
      this.scene.add(channel)
      this.outputChannels.push(channel)
    })
  }

  createTrucks() {
    const truckPositions = [
      { x: 18, z: -5, color: 0x5c6bc0 },
      { x: 18, z: 0, color: 0x66bb6a },
      { x: 18, z: 5, color: 0xffa726 }
    ]

    truckPositions.forEach((pos, index) => {
      const truck = new THREE.Group()

      // Truck cargo box - industrial container
      const bodyGeometry = new THREE.BoxGeometry(3, 2.5, 2.5)
      const bodyMaterial = new THREE.MeshStandardMaterial({ 
        color: pos.color,
        roughness: 0.5,
        metalness: 0.4
      })
      const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
      body.position.y = 1.75
      body.castShadow = true
      truck.add(body)

      // Truck cab - dark gray
      const cabGeometry = new THREE.BoxGeometry(1.2, 2, 2.3)
      const cabMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x424242,
        roughness: 0.5,
        metalness: 0.4
      })
      const cab = new THREE.Mesh(cabGeometry, cabMaterial)
      cab.position.set(2, 1.5, 0)
      cab.castShadow = true
      truck.add(cab)

      // Windshield
      const windshieldGeometry = new THREE.BoxGeometry(0.05, 0.8, 1.8)
      const windshieldMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x90caf9,
        roughness: 0.1,
        metalness: 0.8,
        transparent: true,
        opacity: 0.6
      })
      const windshield = new THREE.Mesh(windshieldGeometry, windshieldMaterial)
      windshield.position.set(2.6, 1.8, 0)
      truck.add(windshield)

      // Wheels - industrial black
      const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16)
      const wheelMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x2a2a2a,
        roughness: 0.8,
        metalness: 0.2
      })

      const positions = [
        [-1, 0.4, -1.3],
        [-1, 0.4, 1.3],
        [1.5, 0.4, -1.3],
        [1.5, 0.4, 1.3]
      ]

      positions.forEach(wheelPos => {
        const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial)
        wheel.rotation.z = Math.PI / 2
        wheel.position.set(...wheelPos)
        wheel.castShadow = true
        truck.add(wheel)
      })

      truck.position.set(pos.x, 0, pos.z)
      truck.userData.index = index
      
      this.scene.add(truck)
      this.trucks.push(truck)
    })
  }

  createComponent(type) {
    let geometry, material, mesh

    switch (type) {
      case 'capacitor':
        // Cylindrical capacitor
        geometry = new THREE.CylinderGeometry(0.2, 0.2, 0.6, 16)
        material = new THREE.MeshStandardMaterial({ 
          color: 0x409eff,
          roughness: 0.4,
          metalness: 0.5
        })
        break
      case 'terminal':
        // Rectangular terminal
        geometry = new THREE.BoxGeometry(0.5, 0.3, 0.4)
        material = new THREE.MeshStandardMaterial({ 
          color: 0x67c23a,
          roughness: 0.3,
          metalness: 0.7
        })
        break
      case 'connector':
        // L-shaped connector
        geometry = new THREE.BoxGeometry(0.6, 0.2, 0.3)
        material = new THREE.MeshStandardMaterial({ 
          color: 0xe6a23c,
          roughness: 0.4,
          metalness: 0.6
        })
        break
      default:
        geometry = new THREE.BoxGeometry(0.4, 0.4, 0.4)
        material = new THREE.MeshStandardMaterial({ color: 0x95a5a6 })
    }

    mesh = new THREE.Mesh(geometry, material)
    mesh.castShadow = true
    mesh.userData.type = type
    mesh.userData.state = 'conveying' // conveying, identified, sorting, sorted, picked
    mesh.userData.targetChannel = null
    mesh.userData.pickupTime = 0
    mesh.userData.sortStartTime = null
    mesh.userData.isAttachedToGripper = false
    mesh.userData.releaseStartTime = null
    mesh.userData.releaseFrom = null
    mesh.userData.dropPos = null
    mesh.userData.originalEmissive = null

    // Random position on conveyor start
    mesh.position.set(-19, 0.8, (Math.random() - 0.5) * 2)
    
    this.scene.add(mesh)
    this.components.push(mesh)
    
    return mesh
  }

  setupControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.05
    this.controls.maxPolarAngle = Math.PI / 2.2
    this.controls.minDistance = 10
    this.controls.maxDistance = 50
  }

  start() {
    this.isRunning = true
    this.isPaused = false
    this.animationPhase = 'delivering'
    this.store.setPhase('delivering')
  }

  pause() {
    this.isPaused = true
  }

  resume() {
    this.isPaused = false
  }

  stop() {
    this.isRunning = false
    this.isPaused = false
    this.animationPhase = 'idle'
    this.store.setPhase('idle')
    
    // Clear all components
    this.components.forEach(comp => {
      this.scene.remove(comp)
    })
    this.components = []
    this.componentSpawnTimer = 0
  }

  updateComponents(delta) {
    if (!this.isRunning || this.isPaused) return

    // Spawn new components
    this.componentSpawnTimer += delta
    if (this.componentSpawnTimer >= this.componentSpawnInterval) {
      this.componentSpawnTimer = 0
      const type = this.componentTypes[Math.floor(Math.random() * this.componentTypes.length)]
      this.createComponent(type)
    }

    // Update component positions
    this.components.forEach((comp, index) => {
      if (comp.userData.state === 'conveying') {
        // Move along conveyor belt
        comp.position.x += 3 * delta
        
        // Identify at camera position
        if (comp.position.x >= -1 && comp.position.x <= 1) {
          comp.userData.state = 'identified'
          this.store.setPhase('identifying')
          
          // Determine target channel based on type
          if (comp.userData.type === 'capacitor') {
            comp.userData.targetChannel = 0
          } else if (comp.userData.type === 'terminal') {
            comp.userData.targetChannel = 1
          } else if (comp.userData.type === 'connector') {
            comp.userData.targetChannel = 2
          }
        }
        
        // Remove if off the belt
        if (comp.position.x > 10) {
          this.scene.remove(comp)
          this.components.splice(index, 1)
        }
      } else if (comp.userData.state === 'identified') {
        // Move to pickup position smoothly
        const targetX = 4.5
        const targetZ = 0
        
        // Smooth interpolation to pickup position
        const speed = 2.5 * delta
        comp.position.x += Math.min(speed, Math.max(0, targetX - comp.position.x))
        comp.position.z += (targetZ - comp.position.z) * 5 * delta

        // Enter sorting without any snapping/teleporting.
        const dx = comp.position.x - targetX
        const dz = comp.position.z - targetZ
        if (Math.abs(dx) <= 0.03 && Math.abs(dz) <= 0.03) {
          const hasActiveArmJob = this.components.some(c => c.userData.state === 'sorting' || c.userData.state === 'releasing')
          if (!hasActiveArmJob) {
            comp.userData.state = 'sorting'
            this.store.setPhase('sorting')
            comp.userData.sortStartTime = this.clock.getElapsedTime()
            comp.userData.pickupTime = comp.userData.sortStartTime
            comp.userData.isAttachedToGripper = false
            comp.userData.releaseStartTime = null
            comp.userData.releaseFrom = null
            comp.userData.dropPos = null
          }
        }
      } else if (comp.userData.state === 'sorting') {
        // Sorting MUST be done by the robotic arm grabbing the component (no teleporting).
        if (comp.userData.sortStartTime == null) {
          comp.userData.sortStartTime = this.clock.getElapsedTime()
          comp.userData.pickupTime = comp.userData.sortStartTime
        }

        const elapsed = this.clock.getElapsedTime() - comp.userData.sortStartTime

        // Pre-calculate drop position only once.
        if (!comp.userData.dropPos) {
          const channelPositions = [
            new THREE.Vector3(11.5, 0.8, -5), // capacitor
            new THREE.Vector3(11.5, 0.8, 0),  // terminal
            new THREE.Vector3(11.5, 0.8, 5)   // connector
          ]
          comp.userData.dropPos = channelPositions[comp.userData.targetChannel]?.clone() || new THREE.Vector3(11.5, 0.8, 0)
        }

        // Attach/release are driven by the arm controller (keeps timing consistent with the visible arm motion).
        const signals = this.armSignals

        if (signals?.shouldAttach && !comp.userData.isAttachedToGripper) {
          this.attachComponentToGripper(comp)
        }

        if (signals?.shouldRelease && comp.userData.releaseStartTime == null) {
          comp.userData.releaseStartTime = this.clock.getElapsedTime()
          comp.userData.releaseFrom = this.getWorldPositionSafe(comp).clone()
          this.detachComponentToScene(comp)
          comp.userData.state = 'releasing'
        }
      } else if (comp.userData.state === 'picking') {
        // Animate pickup and move to truck
        const elapsed = this.clock.getElapsedTime() - comp.userData.pickupTime
        const targetTruck = this.trucks[comp.userData.targetChannel]
        
        if (elapsed < 1) {
          const progress = elapsed
          comp.position.x = comp.position.x + (targetTruck.position.x - comp.position.x) * progress * 0.3
          comp.position.y = 0.8 + Math.sin(progress * Math.PI) * 1.5
          comp.position.z = comp.position.z + (targetTruck.position.z - comp.position.z) * progress * 0.3
        } else {
          // Picked up - remove component
          this.scene.remove(comp)
          const idx = this.components.indexOf(comp)
          if (idx > -1) {
            this.components.splice(idx, 1)
          }
        }
      } else if (comp.userData.state === 'releasing') {
        // Smoothly place the component into its output channel after gripper release.
        const t0 = comp.userData.releaseStartTime ?? this.clock.getElapsedTime()
        const elapsed = this.clock.getElapsedTime() - t0
        const duration = 0.25
        const progress = Math.min(1, elapsed / duration)
        const eased = this.easeInOutCubic(progress)

        const from = comp.userData.releaseFrom || comp.position.clone()
        const to = comp.userData.dropPos || comp.position.clone()

        comp.position.set(
          from.x + (to.x - from.x) * eased,
          from.y + (to.y - from.y) * eased,
          from.z + (to.z - from.z) * eased
        )
        comp.rotation.set(0, 0, 0)

        // Reset scale to normal as component is released
        const scaleProgress = Math.min(1, progress * 2)
        comp.scale.setScalar(1.05 - 0.05 * scaleProgress)

        if (!comp.userData.originalEmissive) {
          comp.userData.originalEmissive = comp.material.emissive ? comp.material.emissive.clone() : new THREE.Color(0x000000)
        }
        if (comp.material.emissive) {
          comp.material.emissive = new THREE.Color(0x409eff)
          comp.material.emissiveIntensity = 0.5 * (1 - eased)
        }

        if (progress >= 1) {
          // Final stable position in channel
          comp.position.copy(to)
          if (comp.userData.originalEmissive && comp.material.emissive) {
            comp.material.emissive.copy(comp.userData.originalEmissive)
            comp.material.emissiveIntensity = 0
          }

          comp.userData.state = 'sorted'
          
          // Debug: Log component sorting
          console.log('Component sorted:', comp.userData.type, 'Total before:', this.store.totalComponents)
          this.store.incrementComponent(comp.userData.type)
          console.log('Total after:', this.store.totalComponents, 'Capacitors:', this.store.sortedCapacitors, 'Terminals:', this.store.sortedTerminals, 'Connectors:', this.store.sortedConnectors)

          setTimeout(() => {
            if (comp.parent) {
              comp.userData.state = 'picking'
              this.store.setPhase('picking')
              comp.userData.pickupTime = this.clock.getElapsedTime()
            }
          }, 600)
        }
      }
    })
  }

  animateBeltLines(delta) {
    if (!this.isRunning || this.isPaused) return
    
    this.scene.children.forEach(child => {
      if (child.userData.isBeltLine) {
        child.position.x += 2 * delta
        if (child.position.x > 11) {
          child.position.x = -19
        }
      }
    })
  }

  animateScanLight(time) {
    if (!this.camera3D) return

    const hasIdentifyingComponents = this.components.some(c => c.userData.state === 'identified' || 
      (c.userData.state === 'conveying' && c.position.x >= -2 && c.position.x <= 2))

    if (hasIdentifyingComponents && this.isRunning && !this.isPaused) {
      // Active scanning animation
      const pulseIntensity = 1.5 + Math.sin(time * 8) * 0.8
      const pulseOpacity = 0.2 + Math.sin(time * 8) * 0.15
      const ringScale = 1 + Math.sin(time * 6) * 0.3
      const ringOpacity = 0.4 + Math.sin(time * 6) * 0.4

      // Animate main spotlight
      if (this.camera3D.scanLight) {
        this.camera3D.scanLight.intensity = pulseIntensity
      }

      // Animate point lights
      if (this.camera3D.scanPointLight1) {
        this.camera3D.scanPointLight1.intensity = pulseIntensity * 0.6
      }
      if (this.camera3D.scanPointLight2) {
        this.camera3D.scanPointLight2.intensity = pulseIntensity * 0.6
      }

      // Animate scan beam
      if (this.camera3D.scanBeam) {
        this.camera3D.scanBeam.material.opacity = pulseOpacity
        this.camera3D.scanBeam.scale.set(1, 1 + Math.sin(time * 4) * 0.1, 1)
      }

      // Animate scan ring
      if (this.camera3D.scanRing) {
        this.camera3D.scanRing.scale.set(ringScale, ringScale, 1)
        this.camera3D.scanRing.material.opacity = ringOpacity
        this.camera3D.scanRing.rotation.z = time * 2
      }

      // Animate scanning laser line
      if (this.camera3D.scanLaser) {
        this.camera3D.scanLaser.visible = true
        const laserOpacity = 0.6 + Math.sin(time * 10) * 0.4
        this.camera3D.scanLaser.material.opacity = laserOpacity
        // Move laser up and down
        this.camera3D.scanLaser.position.y = 0.7 + Math.sin(time * 5) * 0.15
        // Rotate laser slightly
        this.camera3D.scanLaser.rotation.z = Math.sin(time * 3) * 0.1
      }
    } else {
      // Idle state - subtle breathing effect
      const idleIntensity = 0.3 + Math.sin(time * 2) * 0.15
      const idleOpacity = 0.08 + Math.sin(time * 2) * 0.05

      if (this.camera3D.scanLight) {
        this.camera3D.scanLight.intensity = idleIntensity
      }
      if (this.camera3D.scanPointLight1) {
        this.camera3D.scanPointLight1.intensity = idleIntensity * 0.5
      }
      if (this.camera3D.scanPointLight2) {
        this.camera3D.scanPointLight2.intensity = idleIntensity * 0.5
      }
      if (this.camera3D.scanBeam) {
        this.camera3D.scanBeam.material.opacity = idleOpacity
      }
      if (this.camera3D.scanRing) {
        this.camera3D.scanRing.material.opacity = 0.2
        this.camera3D.scanRing.rotation.z = time * 0.5
      }
      // Hide laser in idle state
      if (this.camera3D.scanLaser) {
        this.camera3D.scanLaser.visible = false
      }
    }
  }

  animateRoboticArm(time) {
    // The robotic hand motion is managed by RoboticArmController.
    const sortingComp = this.components.find(c => c.userData.state === 'sorting')
    if (sortingComp && this.isRunning && !this.isPaused) {
      this.armSignals = this.armController?.update({
        time,
        isActive: true,
        sortStartTime: sortingComp.userData.sortStartTime,
        pickup: new THREE.Vector3(4.5, 0.8, 0),
        drop: sortingComp.userData.dropPos,
        targetChannel: sortingComp.userData.targetChannel
      }) || { phase: 'idle', shouldAttach: false, shouldRelease: false }
    } else {
      this.armSignals = this.armController?.update({ time, isActive: false }) || { phase: 'idle', shouldAttach: false, shouldRelease: false }
    }

    // No arm segments to animate - only the hand moves
  }

  getWorldPositionSafe(obj) {
    const v = new THREE.Vector3()
    if (!obj) return v
    obj.getWorldPosition(v)
    return v
  }

  attachComponentToGripper(comp) {
    if (!this.gripperTip || !comp || comp.userData.isAttachedToGripper) return

    const worldPos = this.getWorldPositionSafe(comp)

    // Ensure matrices are up-to-date before converting coordinates.
    this.roboticHand?.updateMatrixWorld?.(true)
    this.gripperTip.updateMatrixWorld(true)

    // Move under gripperTip while preserving current world position (no jump).
    this.scene.attach(comp) // normalize parent to scene first
    this.gripperTip.attach(comp)
    comp.position.copy(this.gripperTip.worldToLocal(worldPos))
    comp.rotation.set(0, 0, 0)

    // Visual "grabbed" cue - stronger glow effect
    if (!comp.userData.originalEmissive) {
      comp.userData.originalEmissive = comp.material.emissive ? comp.material.emissive.clone() : new THREE.Color(0x000000)
    }
    if (comp.material.emissive) {
      comp.material.emissive = new THREE.Color(0x409eff)
      comp.material.emissiveIntensity = 0.5
    }

    // Add a subtle scale pulse to show grip
    comp.scale.setScalar(1.05)

    comp.userData.isAttachedToGripper = true
  }

  detachComponentToScene(comp) {
    if (!comp) return
    // Ensure it ends up directly under scene to avoid inheriting arm transforms.
    this.scene.attach(comp)
    comp.userData.isAttachedToGripper = false
  }
  
  // Easing functions for smoother animations
  easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
  }
  
  easeOutBack(t) {
    const c1 = 1.70158
    const c3 = c1 + 1
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
  }

  animate() {
    requestAnimationFrame(() => this.animate())
    
    const delta = this.clock.getDelta()
    const time = this.clock.getElapsedTime()

    this.updateComponents(delta)
    this.animateBeltLines(delta)
    this.animateScanLight(time)
    this.animateRoboticArm(time)
    
    if (this.controls) {
      this.controls.update()
    }
    
    this.renderer.render(this.scene, this.camera)
  }

  destroy() {
    if (this.renderer) {
      this.renderer.dispose()
      this.container.removeChild(this.renderer.domElement)
    }
    if (this.controls) {
      this.controls.dispose()
    }
  }
}

export default SortingScene
