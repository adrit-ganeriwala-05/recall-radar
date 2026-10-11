"use client";
// Owner: C. The single owner of camera and model transforms (ARCHITECTURE.md §5).
// Reads the mutable MotionState, damps the current framing toward the active composition, and keeps
// requesting frames (frameloop="demand") only until the motion settles. Pointer influence is a small,
// clamped additive yaw/pitch on the model group; it never moves the camera. Nothing else writes these.
import { useFrame, useThree } from "@react-three/fiber";
import { useRef, type ReactNode } from "react";
import { MathUtils, PerspectiveCamera, Vector3, type Group } from "three";
import { compositionFor, fitDistance, type MotionState } from "./motionState";

const DAMPING = 3.2; // per second; higher = snappier
const POINTER_YAW = 0.07; // radians at the viewport edge
const POINTER_PITCH = 0.025;
const SETTLED = 1e-4;

type Framing = { pos: Vector3; target: Vector3; fov: number; ax: number; ay: number; yaw: number; pitch: number };

type Props = {
  motion: MotionState;
  /** Measured bounding-sphere radius of the normalized model (see VehicleModel). */
  radius: { current: number };
  children: ReactNode;
};

export function SceneController({ motion, radius, children }: Props) {
  const camera = useThree((s) => s.camera) as PerspectiveCamera;
  const size = useThree((s) => s.size);
  const invalidate = useThree((s) => s.invalidate);
  const model = useRef<Group>(null);
  const current = useRef<Framing | null>(null);
  const goalPos = useRef(new Vector3());
  const goalTarget = useRef(new Vector3());

  useFrame((_, delta) => {
    const comp = compositionFor(motion.chapter, size.width);
    goalTarget.current.set(...comp.target);
    // Camera = target + direction * distance, with the distance solved from the measured model size.
    const distance = fitDistance(radius.current, comp.fill, comp.fov, size.width / Math.max(1, size.height));
    goalPos.current.set(...comp.direction).normalize().multiplyScalar(distance).add(goalTarget.current);
    const still = motion.reducedMotion;
    const yawGoal = comp.yaw + (still ? 0 : motion.pointer.x * POINTER_YAW);
    const pitchGoal = still ? 0 : motion.pointer.y * POINTER_PITCH;

    let cur = current.current;
    if (!cur) {
      cur = current.current = {
        pos: goalPos.current.clone(),
        target: goalTarget.current.clone(),
        fov: comp.fov,
        ax: comp.anchor.x,
        ay: comp.anchor.y,
        yaw: yawGoal,
        pitch: pitchGoal,
      };
    }

    // Reduced motion snaps to the goal; otherwise frame-rate independent exponential damping.
    const dt = Math.min(delta, 0.1);
    const step = (a: number, b: number) => (still ? b : MathUtils.damp(a, b, DAMPING, dt));
    cur.pos.set(step(cur.pos.x, goalPos.current.x), step(cur.pos.y, goalPos.current.y), step(cur.pos.z, goalPos.current.z));
    cur.target.set(
      step(cur.target.x, goalTarget.current.x),
      step(cur.target.y, goalTarget.current.y),
      step(cur.target.z, goalTarget.current.z),
    );
    cur.fov = step(cur.fov, comp.fov);
    cur.ax = step(cur.ax, comp.anchor.x);
    cur.ay = step(cur.ay, comp.anchor.y);
    cur.yaw = step(cur.yaw, yawGoal);
    cur.pitch = step(cur.pitch, pitchGoal);

    camera.position.copy(cur.pos);
    camera.fov = cur.fov;
    camera.lookAt(cur.target);
    // Shift the projected image so the car's centre lands at the composition's screen anchor without
    // moving the camera (keeps perspective identical across layouts).
    camera.setViewOffset(size.width, size.height, (0.5 - cur.ax) * size.width, (0.5 - cur.ay) * size.height, size.width, size.height);
    camera.updateProjectionMatrix();
    if (model.current) {
      model.current.rotation.set(cur.pitch, cur.yaw, 0);
    }

    const residual =
      cur.pos.distanceTo(goalPos.current) +
      cur.target.distanceTo(goalTarget.current) +
      Math.abs(cur.fov - comp.fov) +
      Math.abs(cur.ax - comp.anchor.x) +
      Math.abs(cur.ay - comp.anchor.y) +
      Math.abs(cur.yaw - yawGoal) +
      Math.abs(cur.pitch - pitchGoal);
    // Keep rendering while damping is still moving things; stop when settled or when the tab is hidden.
    if (residual > SETTLED && !document.hidden) invalidate();
  });

  return <group ref={model}>{children}</group>;
}
