"use client";
// Owner: C. Loads the licensed illustrative vehicle and normalizes it from its own bounding box.
// Asset: public/models/car-concept-pearl.glb, derived from Khronos glTF Sample Assets "Car Concept"
// (CC BY 4.0, Eric Chadwick / Darmstadt Graphics Group) — see public/models/ATTRIBUTION.md.
// Loaded with three's own GLTFLoader (current support for clearcoat, iridescence, transmission) and
// three's bundled meshopt decoder; no Draco, so no decoder is fetched from a CDN.
import { useLoader } from "@react-three/fiber";
import { useEffect } from "react";
import { Box3, Mesh, MeshPhysicalMaterial, MeshStandardMaterial, Sphere, Vector3, type Material, type Object3D } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";

export const MODEL_URL = `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/models/car-concept-pearl.glb`;

/** Name of the vehicle's root group (SceneController measures the car alone, not its shadow plane). */
export const VEHICLE_NODE = "rr-vehicle";

/** Normalized car length in scene units; COMPOSITIONS in motionState.ts are authored for this. */
export const TARGET_LENGTH = 4;

type Normalization = { scale: number; offset: [number, number, number]; radius: number };

function configureLoader(loader: GLTFLoader) {
  loader.setMeshoptDecoder(MeshoptDecoder);
}

/**
 * Measured once on the freshly parsed scene and cached on it. Computing it again on a remount would
 * be wrong: the cached scene may still be attached to the previous (scaled) parent.
 */
function normalization(scene: Object3D): Normalization {
  const cached = scene.userData.rrNormalization as Normalization | undefined;
  if (cached) return cached;
  const box = new Box3().setFromObject(scene);
  const size = box.getSize(new Vector3());
  const center = box.getCenter(new Vector3());
  // Nose points along +z (measured: headlights at z = +2.18 m), so length is the z extent.
  const scale = TARGET_LENGTH / size.z;
  // Bounding-sphere radius in normalized units: SceneController solves camera distance from it.
  const radius = box.getBoundingSphere(new Sphere()).radius * scale;
  const result: Normalization = { scale, offset: [-center.x, -box.min.y, -center.z], radius };
  scene.userData.rrNormalization = result;
  return result;
}

/**
 * Art direction for the brief's pearl-silver car: the upstream "Pearly Swirly" paints use
 * iridescence (an oil-slick purple/green), so the two body paints are retuned to a light silver with
 * clearcoat and no iridescence. Recorded as a modification in public/models/ATTRIBUTION.md.
 */
const PEARL_SILVER: Record<string, { color: string; roughness: number }> = {
  "Paint 1 Pearl": { color: "#d6d8da", roughness: 0.3 },
  "Paint 2 Pearl": { color: "#a9adb2", roughness: 0.34 },
};

function applyPearlSilver(scene: Object3D) {
  if (scene.userData.rrPearlSilver) return;
  scene.traverse((obj) => {
    if (!(obj instanceof Mesh)) return;
    const mats: Material[] = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const m of mats) {
      const look = PEARL_SILVER[m.name];
      // "Paint 2 Pearl" has no clearcoat extension, so GLTFLoader makes it a MeshStandardMaterial.
      if (!look || !(m instanceof MeshStandardMaterial)) continue;
      m.color.set(look.color);
      m.metalness = 0.75;
      m.roughness = look.roughness;
      if (m instanceof MeshPhysicalMaterial) {
        m.iridescence = 0;
        m.iridescenceThicknessMap = null;
        m.clearcoat = 1;
        m.clearcoatRoughness = 0.06;
      }
      m.needsUpdate = true;
    }
  });
  scene.userData.rrPearlSilver = true;
}

/** Low tier: replace transmission glass (an extra scene render per frame) with tinted transparency. */
function simplifyGlass(scene: Object3D) {
  if (scene.userData.rrGlassSimplified) return;
  scene.traverse((obj) => {
    if (!(obj instanceof Mesh)) return;
    const mats: Material[] = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const m of mats) {
      if (m instanceof MeshPhysicalMaterial && m.transmission > 0) {
        m.transmission = 0;
        m.transparent = true;
        m.opacity = 0.3;
        m.depthWrite = false;
        m.color.set("#20252b");
        m.needsUpdate = true;
      }
    }
  });
  scene.userData.rrGlassSimplified = true;
}

type Props = { transmission: boolean; onReady: (radius: number) => void };

export function VehicleModel({ transmission, onReady }: Props) {
  const gltf = useLoader(GLTFLoader, MODEL_URL, configureLoader);
  const { scale, offset, radius } = normalization(gltf.scene);
  applyPearlSilver(gltf.scene);
  if (!transmission) simplifyGlass(gltf.scene);

  useEffect(() => {
    onReady(radius);
  }, [onReady, radius]);

  // The cached scene is shared with useLoader's cache: R3F does not dispose <primitive> objects,
  // so unmount/remount (Strict Mode, route changes) reuses it safely.
  return (
    <group name={VEHICLE_NODE} scale={scale}>
      <group position={offset}>
        <primitive object={gltf.scene} />
      </group>
    </group>
  );
}

/** Start the download as soon as the scene chunk loads (browser only; this module is client-only). */
useLoader.preload(GLTFLoader, MODEL_URL, configureLoader);
