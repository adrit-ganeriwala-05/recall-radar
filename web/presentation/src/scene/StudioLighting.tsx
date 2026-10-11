"use client";
// Owner: C. Soft studio light without remote HDR files: an environment map rendered once from
// in-scene light panels (drei Lightformer), one key and one fill light, no real-time shadow maps.
import { Environment, Lightformer } from "@react-three/drei";

export function StudioLighting() {
  return (
    <>
      <ambientLight intensity={0.12} />
      <directionalLight position={[5, 8, 6]} intensity={1.3} />
      <directionalLight position={[-6, 3, -4]} intensity={0.35} />
      <Environment resolution={256} frames={1} environmentIntensity={1.15}>
        {/* overhead softbox: long, even highlight along the roof and hood */}
        <Lightformer form="rect" intensity={3.2} position={[0, 6, 0]} rotation-x={Math.PI / 2} scale={[10, 4, 1]} />
        {/* side strips: the reflections that read as "silver" on the doors */}
        <Lightformer form="rect" intensity={2.0} position={[7, 1.6, 3]} rotation-y={-Math.PI / 2.4} scale={[9, 1.1, 1]} />
        <Lightformer form="rect" intensity={1.1} position={[-7, 1.6, -2]} rotation-y={Math.PI / 2} scale={[9, 1.1, 1]} />
        {/* low front fill so the nose and bumper are not lost against the graphite background */}
        <Lightformer form="rect" intensity={0.9} position={[3, 0.8, 8]} rotation-y={Math.PI} scale={[8, 1.6, 1]} />
        {/* faint back ring for a rim highlight; the cobalt accent stays in the HTML only */}
        <Lightformer form="ring" intensity={0.5} position={[0, 3, -9]} scale={4} />
      </Environment>
    </>
  );
}
