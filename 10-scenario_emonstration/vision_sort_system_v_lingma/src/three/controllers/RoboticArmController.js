import * as THREE from 'three'

export default class RoboticArmController {
  constructor({
    handGroup,
    gripperTip,
    gripperFingers,
    homePosition = new THREE.Vector3(4.5, 3.2, 0)
  }) {
    this.handGroup = handGroup
    this.gripperTip = gripperTip
    this.gripperFingers = gripperFingers

    this.homePosition = homePosition.clone()

    this._tmp = {
      desired: new THREE.Vector3()
    }
  }

  /**
   * Drives the full arm animation for a sorting job.
   * Returns timing signals for grab/release.
   */
  update({ time, isActive, sortStartTime, pickup, drop, targetChannel }) {
    if (!this.handGroup || !this.gripperTip || !this.gripperFingers) {
      return { phase: 'idle', shouldAttach: false, shouldRelease: false, jointAngles: null }
    }

    if (!isActive || sortStartTime == null || !pickup || !drop) {
      this.updateIdlePose(time)
      return { phase: 'idle', shouldAttach: false, shouldRelease: false, jointAngles: null }
    }

    const elapsed = time - sortStartTime
    const signals = this.updateSortingPose({ elapsed, pickup, drop, targetChannel })
    return signals
  }

  updateIdlePose(time) {
    const { leftFinger, rightFinger } = this.gripperFingers

    leftFinger.position.z += (-0.25 - leftFinger.position.z) * 0.1
    rightFinger.position.z += (0.25 - rightFinger.position.z) * 0.1

    // Only the hand moves; keep it gently at home.
    const breatheY = Math.sin(time * 1.2) * 0.05
    this.handGroup.position.lerp(this.homePosition.clone().add(new THREE.Vector3(0, breatheY, 0)), 0.08)
  }

  updateSortingPose({ elapsed, pickup, drop, targetChannel }) {
    const { leftFinger, rightFinger } = this.gripperFingers

    const liftY = Math.max(pickup.y + 2.7, 3.5)
    const arcY = Math.max(liftY + 1.3, 5.0)

    // Phase definitions (seconds)
    // 0.00-0.20 approach pickup (open)
    // 0.20-0.35 close + lift start (attach signal)
    // 0.35-0.65 move to above drop with arc
    // 0.65-0.80 lower + open (release signal at 0.65)
    // 0.80-1.00 return home
    let phase = 'approach'
    let desired = this._tmp.desired
    let shouldAttach = false
    let shouldRelease = false

    if (elapsed < 0.2) {
      phase = 'approach'
      const t = this.easeInOutCubic(elapsed / 0.2)
      desired.copy(pickup)
      desired.y = pickup.y + (liftY - pickup.y) * (t * 0.15) // tiny pre-lift
      this.handGroup.rotation.y = 0

      // Open gripper wider to receive component
      const fingerOffset = 0.35 - t * 0.15
      leftFinger.position.z = -fingerOffset
      rightFinger.position.z = fingerOffset
    } else if (elapsed < 0.35) {
      phase = 'grab'
      const t = this.easeOutBack((elapsed - 0.2) / 0.15)
      desired.copy(pickup)
      desired.y = pickup.y + (liftY - pickup.y) * t

      // Close gripper firmly
      const fingerOffset = 0.20 - t * 0.10
      leftFinger.position.z = -fingerOffset
      rightFinger.position.z = fingerOffset

      shouldAttach = elapsed >= 0.28
    } else if (elapsed < 0.65) {
      phase = 'carry'
      const raw = (elapsed - 0.35) / 0.3
      const t = this.easeInOutCubic(raw)

      // Interpolate to drop in X/Z
      desired.set(
        pickup.x + (drop.x - pickup.x) * t,
        liftY,
        pickup.z + (drop.z - pickup.z) * t
      )

      // Arc in Y
      const arcFactor = Math.sin(raw * Math.PI)
      desired.y = liftY + arcFactor * (arcY - liftY)
      // Slight yaw to show "aiming" but only on the hand module.
      const yaw = targetChannel === 0 ? -0.35 : targetChannel === 2 ? 0.35 : 0
      this.handGroup.rotation.y = yaw

      // Keep gripper firmly closed
      leftFinger.position.z = -0.10
      rightFinger.position.z = 0.10
    } else if (elapsed < 0.8) {
      phase = 'place'
      const t = this.easeInOutCubic((elapsed - 0.65) / 0.15)
      desired.copy(drop)
      desired.y = liftY + (drop.y - liftY) * t

      // Open gripper wide to release
      const fingerOffset = 0.10 + this.easeOutBack(t) * 0.20
      leftFinger.position.z = -fingerOffset
      rightFinger.position.z = fingerOffset

      shouldRelease = elapsed >= 0.65
    } else if (elapsed < 1.0) {
      phase = 'return'
      const t = this.easeInOutCubic((elapsed - 0.8) / 0.2)
      desired.copy(drop).lerp(this.homePosition, t)
      this.handGroup.rotation.y *= (1 - t)

      // Keep gripper fully open
      leftFinger.position.z = -0.25
      rightFinger.position.z = 0.25
    } else {
      phase = 'done'
      // Return to home position smoothly
      desired.copy(this.homePosition)
      leftFinger.position.z = -0.25
      rightFinger.position.z = 0.25
      this.handGroup.rotation.y = 0
    }

    // Only move the hand module (arm base is fixed).
    this.handGroup.position.copy(desired)

    return {
      phase,
      shouldAttach,
      shouldRelease,
      jointAngles: this.computeLinkedJointAngles(desired, targetChannel)
    }
  }

  /**
   * Compute visually plausible joint angles linked to the hand position.
   * Note: This is not a full IK solver; it's a stable mapping that makes the arm "follow" the hand.
   */
  computeLinkedJointAngles(handWorldPos, targetChannel = 1) {
    if (!handWorldPos) return null

    // Use the hand position relative to its home to drive "reach" and "side" motion.
    const dx = handWorldPos.x - this.homePosition.x // forward/back
    const dz = handWorldPos.z - this.homePosition.z // left/right
    const dy = handWorldPos.y - this.homePosition.y // up/down

    const reach = THREE.MathUtils.clamp(dx / 7, -1, 1)
    const side = THREE.MathUtils.clamp(dz / 6, -1, 1)
    const lift = THREE.MathUtils.clamp(dy / 3, -1, 1)

    // Base pose angles (MUST match the modeled static arm geometry in SortingScene)
    const baseLower = 0
    const baseUpper = Math.PI / 3  // 60 degrees - matches upperArm initial rotation
    const baseFore = Math.PI / 6   // 30 degrees - matches forearm initial rotation

    // Linked deltas - stronger response for more visible arm movement
    const shoulderDelta = (-0.35 * reach) + (0.15 * lift) + (0.15 * side)
    const upperDelta = (-0.25 * reach) + (0.15 * lift) - (0.08 * side)
    const foreDelta = (0.15 * reach) + (0.12 * lift) - (0.12 * side)

    // Extra slight "aim" by channel to make the linkage clearer.
    const channelBias = targetChannel === 0 ? -0.12 : targetChannel === 2 ? 0.12 : 0

    return {
      lowerArmZ: baseLower + shoulderDelta + channelBias,
      upperArmZ: baseUpper + upperDelta,
      forearmZ: baseFore + foreDelta - channelBias
    }
  }

  easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
  }

  easeOutBack(t) {
    const c1 = 1.70158
    const c3 = c1 + 1
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
  }
}

