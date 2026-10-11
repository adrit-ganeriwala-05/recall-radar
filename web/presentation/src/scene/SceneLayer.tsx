"use client";
// Owner: C. Layer 1: one persistent R3F <Canvas> with Three.js objects only (no HTML inside it).
// Client-only (imported through next/dynamic with ssr:false from SceneLayerLoader). Failure modes —
// model error, renderer crash, lost WebGL context — swap the canvas for the static fallback; the HTML
// page above keeps working. frameloop="demand": frames render only when SceneController (or a motion
// writer below) asks for one, so an idle page and hidden tabs cost nothing.
import { ContactShadows } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SceneFrame } from "@/components/SceneFrame";
import { StaticVehicleFallback } from "@/components/StaticVehicleFallback";
import { CHAPTERS, DEFAULT_MODEL_RADIUS, type ChapterId } from "./motionState";
import { getSceneKind, motion, setFrameRequester, setSceneKind } from "./motionStore";
import { detectQuality } from "./quality";
import { isSoftwareRenderer, rendererName } from "./renderer";
import { useSceneStage } from "./stage";
import { SceneController, type CarBox } from "./SceneController";
import { SceneErrorBoundary } from "./SceneErrorBoundary";
import { StudioLighting } from "./StudioLighting";
import { VehicleModel } from "./VehicleModel";

type Status = "loading" | "ready" | { failed: string };

/** A model that has not arrived by then is treated as failed: show the static illustration instead. */
export const MODEL_LOAD_TIMEOUT_MS = 45_000;

type Invalidate = () => void;

/** Hands R3F's invalidate() to writers that live outside the Canvas (pointer, inspector). */
function InvalidateBridge({ target }: { target: { current: Invalidate | null } }) {
  const invalidate = useThree((s) => s.invalidate);
  useEffect(() => {
    const request = () => invalidate();
    target.current = request;
    setFrameRequester(request); // writers outside React (ScrollDirector) use motionStore.requestFrame()
    return () => {
      target.current = null;
      setFrameRequester(null);
    };
  }, [invalidate, target]);
  return null;
}

type Inspector = { chapters: readonly ChapterId[]; compose: (chapter: ChapterId) => ChapterId };
type WindowWithInspector = Window & { __observatory?: Inspector };

export default function SceneLayer() {
  const quality = useMemo(detectQuality, []);
  const invalidateRef = useRef<Invalidate | null>(null);
  const radiusRef = useRef(DEFAULT_MODEL_RADIUS);
  const stage = useSceneStage();
  // Published as data-car-box on the frame (no React state): lets tests verify the car never covers copy.
  const publishBox = useCallback((box: CarBox) => {
    const frame = document.querySelector<HTMLElement>("[data-scene-state]");
    frame?.setAttribute("data-car-box", [box.x, box.y, box.width, box.height].map((v) => Math.round(v)).join(","));
    frame?.setAttribute("data-car-viewport", box.viewport);
    // The scroll path this framing settled for ("none" when choreography is off), so tests can wait for it.
    frame?.setAttribute("data-car-path", document.documentElement.dataset.chapterPath ?? "none");
  }, []);
  const [status, setStatus] = useState<Status>("loading");
  // First reason wins: unmounting the canvas after a model error destroys its context on purpose,
  // which would otherwise overwrite the real reason with "context lost".
  const fail = useCallback((reason: string) => setStatus((s) => (typeof s === "object" ? s : { failed: reason })), []);
  const ready = useCallback((radius: number) => {
    radiusRef.current = radius;
    invalidateRef.current?.();
    setStatus((s) => (s === "loading" ? "ready" : s));
  }, []);

  // A layout change (fonts, content, resize) flags the stage; SceneController re-measures it in-frame.
  useEffect(() => {
    motion.stageDirty = true;
    invalidateRef.current?.();
  }, [motion, stage]);

  // The static fallback has no camera: scroll choreography stays off (ScrollDirector reads the kind).
  useEffect(() => {
    if (typeof status === "object") setSceneKind("fallback");
  }, [status]);

  useEffect(() => {
    if (status !== "loading") return;
    const timer = window.setTimeout(() => fail("the 3D model took too long to load"), MODEL_LOAD_TIMEOUT_MS);
    return () => window.clearTimeout(timer);
  }, [status, fail]);

  // Reduced motion (live), mouse-only pointer influence (hardware WebGL only: under software rendering
  // each pointer frame costs the compositor, as scroll frames do), and a frame when the tab is shown.
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const applyMotion = () => {
      motion.reducedMotion = media.matches;
      invalidateRef.current?.();
    };
    const onPointer = (e: PointerEvent) => {
      if (e.pointerType !== "mouse" || getSceneKind() !== "hardware") return;
      motion.pointer.x = Math.max(-1, Math.min(1, (e.clientX / window.innerWidth) * 2 - 1));
      motion.pointer.y = Math.max(-1, Math.min(1, (e.clientY / window.innerHeight) * 2 - 1));
      invalidateRef.current?.();
    };
    const onVisible = () => {
      if (!document.hidden) invalidateRef.current?.();
    };
    applyMotion();
    media.addEventListener("change", applyMotion);
    window.addEventListener("pointermove", onPointer, { passive: true });
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      media.removeEventListener("change", applyMotion);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [motion]);

  // Development-only composition inspector: window.__observatory.compose("explore").
  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;
    const w = window as WindowWithInspector;
    w.__observatory = {
      chapters: CHAPTERS,
      compose(chapter) {
        if (!CHAPTERS.includes(chapter)) throw new Error(`unknown chapter "${chapter}"; one of ${CHAPTERS.join(", ")}`);
        motion.chapter = chapter;
        invalidateRef.current?.();
        return chapter;
      },
    };
    return () => {
      delete w.__observatory;
    };
  }, [motion]);

  if (typeof status === "object") {
    return (
      <SceneFrame state="fallback" stage={stage}>
        <StaticVehicleFallback reason={status.failed} stage={stage} />
      </SceneFrame>
    );
  }

  return (
    <SceneFrame state={status} stage={stage}>
      <SceneErrorBoundary
        fallback={<StaticVehicleFallback reason="the 3D model could not be loaded" stage={stage} />}
        onError={() => fail("the 3D model could not be loaded")}
      >
        <Canvas
          frameloop="demand"
          dpr={quality.dpr}
          gl={{ antialias: quality.antialias, alpha: true, powerPreference: "high-performance" }}
          camera={{ fov: 30, near: 0.1, far: 100, position: [4.6, 1.55, 5.9] }}
          className={`transition-opacity duration-500 motion-reduce:transition-none ${status === "ready" ? "opacity-100" : "opacity-0"}`}
          onCreated={({ gl }) => {
            gl.toneMappingExposure = 1.1;
            setSceneKind(isSoftwareRenderer(rendererName(gl.getContext())) ? "software" : "hardware");
            gl.domElement.addEventListener(
              "webglcontextlost",
              (event) => {
                event.preventDefault();
                fail("the graphics context was lost");
              },
              { once: true },
            );
          }}
        >
          <InvalidateBridge target={invalidateRef} />
          <StudioLighting />
          <SceneController motion={motion} radius={radiusRef} onSettled={publishBox}>
            <Suspense fallback={null}>
              <VehicleModel transmission={quality.transmission} onReady={ready} />
            </Suspense>
            {/* Baked once (frames=1) after the model is in the scene — baking earlier would capture an
                empty floor — and parented to the car, so it turns with the model at no per-frame cost. */}
            {status === "ready" && (
              <ContactShadows
                position={[0, 0.002, 0]}
                scale={[4.4, 7.2]}
                opacity={0.85}
                blur={2.8}
                far={1.6}
                resolution={quality.shadowResolution}
                frames={1}
                color="#000000"
              />
            )}
          </SceneController>
        </Canvas>
      </SceneErrorBoundary>
    </SceneFrame>
  );
}
