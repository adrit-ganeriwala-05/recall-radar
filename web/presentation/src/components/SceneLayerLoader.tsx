"use client";
// Owner: C. Client boundary for the scene. The server HTML contains no scene at all, so text and
// navigation render first; after mount we check WebGL and only then download the 3D code
// (next/dynamic, ssr:false — declared in a Client Component as Next 16 requires).
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { SceneFrame } from "./SceneFrame";
import { useSceneStage } from "@/scene/stage";
import { StaticVehicleFallback } from "./StaticVehicleFallback";

const SceneLayer = dynamic(() => import("@/scene/SceneLayer"), { ssr: false, loading: () => null });

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    // The probe context is left to garbage collection: forcing loseContext() makes Firefox log
    // "WebGL context was lost", and one short-lived extra context is far below browser limits.
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

export function SceneLayerLoader() {
  const [support, setSupport] = useState<"unknown" | "webgl" | "none">("unknown");
  const stage = useSceneStage();

  useEffect(() => {
    setSupport(hasWebGL() ? "webgl" : "none");
  }, []);

  if (support === "unknown") return null;
  if (support === "none") {
    return (
      <SceneFrame state="fallback" stage={stage}>
        <StaticVehicleFallback reason="WebGL is not available in this browser" stage={stage} />
      </SceneFrame>
    );
  }
  return <SceneLayer />;
}
