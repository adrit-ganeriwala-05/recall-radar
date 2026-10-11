"use client";
// Owner: C. The single owner of camera and model transforms (ARCHITECTURE.md §5).
// Reads the mutable MotionState, damps the current framing toward the active composition, and keeps
// requesting frames (frameloop="demand") only until the motion settles. Pointer influence is a small,
// clamped additive yaw/pitch on the model group; it never moves the camera. Nothing else writes these.
import { useFrame, useThree } from "@react-three/fiber";
import { useRef, type ReactNode } from "react";
import { Box3, MathUtils, PerspectiveCamera, Vector3, type Group } from "three";
import { activeComposition, fitDistance, type MotionState } from "./motionState";
import { measureStage, stageFraming } from "./stage";
import { VEHICLE_NODE } from "./VehicleModel";

const DAMPING = 3.2; // per second; higher = snappier
const POINTER_YAW = 0.07; // radians at the viewport edge
const POINTER_PITCH = 0.025;
const SETTLED = 1e-4;

type Framing = { pos: Vector3; target: Vector3; fov: number; ax: number; ay: number; yaw: number; pitch: number };

/** Screen-space box of the car in CSS pixels (published when motion settles; used by tests). */
export type CarBox = { x: number; y: number; width: number; height: number; viewport: string };

type Props = {
  motion: MotionState;
  /** Called once each time the framing settles, with the car's projected screen box. */
  onSettled?: (box: CarBox) => void;
  /** Measured bounding-sphere radius of the normalized model (see VehicleModel). */
  radius: { current: number };
  children: ReactNode;
};

export function SceneController({ motion, radius, onSettled, children }: Props) {
  const camera = useThree((s) => s.camera) as PerspectiveCamera;
  const size = useThree((s) => s.size);
  const invalidate = useThree((s) => s.invalidate);
  const model = useRef<Group>(null);
  const current = useRef<Framing | null>(null);
  const goalPos = useRef(new Vector3());
  const goalTarget = useRef(new Vector3());
  const settled = useRef(false);
  const lastGoal = useRef("");
  const settledOnce = useRef(false);
  const lastSize = useRef("");
  const box = useRef(new Box3());
  const corner = useRef(new Vector3());

  useFrame((_, delta) => {
    // Single writer of motion.stage: re-measure the DOM stage in the same frame the canvas size changes
    // (and when the layer flags a layout change), so the framing never uses the previous layout's stage.
    const sizeKey = `${size.width}x${size.height}`;
    if (sizeKey !== lastSize.current || motion.stageDirty) {
      lastSize.current = sizeKey;
      motion.stageDirty = false;
      const measured = measureStage();
      motion.stage = measured ? stageFraming(measured) : null;
    }
    const comp = activeComposition(motion, size.width);
    goalTarget.current.set(...comp.target);
    // Camera = target + direction * distance, with the distance solved from the measured model size.
    const distance = fitDistance(radius.current, comp.fill, comp.fov, size.width / Math.max(1, size.height));
    goalPos.current.set(...comp.direction).normalize().multiplyScalar(distance).add(goalTarget.current);
    // Snap (no easing) until the first settled framing: before that the car is not visible yet (it fades
    // in), so easing from the default framing to the measured stage would only cost frames on slow devices.
    const still = motion.reducedMotion || !settledOnce.current;
    const yawGoal = comp.yaw + (still ? 0 : motion.pointer.x * POINTER_YAW);
    const pitchGoal = still ? 0 : motion.pointer.y * POINTER_PITCH;

    // A new goal (composition, stage, viewport) needs a new settle report even if it is reached in a
    // single frame (reduced motion snaps), so the published box is never stale.
    const goalKey = `${goalPos.current.toArray().map((v) => v.toFixed(3))}|${comp.anchor.x.toFixed(4)},${comp.anchor.y.toFixed(4)}|${yawGoal.toFixed(3)}|${size.width}x${size.height}`;
    if (goalKey !== lastGoal.current) {
      lastGoal.current = goalKey;
      settled.current = false;
    }

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
    if (residual > SETTLED) {
      settled.current = false;
      if (!document.hidden) invalidate();
    } else if (!settled.current && model.current && onSettled) {
      // Project the model's world box once per settle (not per frame) and report it.
      settled.current = true;
      if (model.current.getObjectByName(VEHICLE_NODE)) settledOnce.current = true;
      model.current.updateWorldMatrix(true, true);
      // The vehicle only: the contact-shadow plane in the same group is much larger than the car.
      const vehicle = model.current.getObjectByName(VEHICLE_NODE);
      box.current.makeEmpty();
      if (vehicle) box.current.setFromObject(vehicle);
      if (!box.current.isEmpty()) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (let i = 0; i < 8; i++) {
          corner.current
            .set(i & 1 ? box.current.max.x : box.current.min.x, i & 2 ? box.current.max.y : box.current.min.y, i & 4 ? box.current.max.z : box.current.min.z)
            .project(camera);
          const sx = ((corner.current.x + 1) / 2) * size.width;
          const sy = ((1 - corner.current.y) / 2) * size.height;
          minX = Math.min(minX, sx); maxX = Math.max(maxX, sx); minY = Math.min(minY, sy); maxY = Math.max(maxY, sy);
        }
        onSettled({ x: minX, y: minY, width: maxX - minX, height: maxY - minY, viewport: `${size.width}x${size.height}` });
      }
    }
  });

  return <group ref={model}>{children}</group>;
}
