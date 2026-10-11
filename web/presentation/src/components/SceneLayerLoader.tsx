"use client";
// Owner: C. Client boundary for the scene. The server HTML contains no scene at all, so text and
// navigation render first; after mount we check WebGL and only then download the 3D code
// (next/dynamic, ssr:false — declared in a Client Component as Next 16 requires).
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { SceneFrame } from "./SceneFrame";
import { StaticVehicleFallback } from "./StaticVehicleFallback";

const SceneLayer = dynamic(() => import("@/scene/SceneLayer"), { ssr: false, loading: () => null });

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    if (!gl) return false;
    gl.getExtension("WEBGL_lose_context")?.loseContext(); // release the probe context immediately
    return true;
  } catch {
    return false;
  }
}

export function SceneLayerLoader() {
  const [support, setSupport] = useState<"unknown" | "webgl" | "none">("unknown");

  useEffect(() => {
    setSupport(hasWebGL() ? "webgl" : "none");
  }, []);

  if (support === "unknown") return null;
  if (support === "none") {
    return (
      <SceneFrame state="fallback">
        <StaticVehicleFallback reason="WebGL is not available in this browser" />
      </SceneFrame>
    );
  }
  return <SceneLayer />;
}
