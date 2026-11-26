import type { Vec3 } from './twinTypes'

export function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v))
}

export function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

export function easeInOutCubic(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

export function vec3(x = 0, y = 0, z = 0): Vec3 {
  return { x, y, z }
}

export function cloneVec3(v: Vec3): Vec3 {
  return { x: v.x, y: v.y, z: v.z }
}

export function formatVec3(v: Vec3) {
  const fx = v.x.toFixed(2)
  const fy = v.y.toFixed(2)
  const fz = v.z.toFixed(2)
  return `(${fx}, ${fy}, ${fz})`
}

