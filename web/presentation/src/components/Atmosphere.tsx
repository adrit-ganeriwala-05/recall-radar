"use client";
// Owner: C. Studio atmosphere behind everything (fixed, z-0, beneath the scene layer; pointer-events
// none). A slow, wispy haze drawn by one fragment shader on its own small WebGL canvas (a fifth of a
// CSS pixel per pixel, upscaled by the browser: haze is soft, so this is invisible and cheap), lit from
// behind the car wherever the camera has placed it and, on mouse devices, softly toward the pointer.
// Static grain sits on top. Motion runs only when it is affordable and wanted: hardware WebGL, no
// reduced-motion preference, tab visible, and something of it on screen; otherwise one still frame.
// Under software WebGL the shader is not used at all (even one frame costs the CPU on every resize),
// and without WebGL, the CSS gradients underneath are the whole effect. Never replaces the cursor.
import { useEffect, useRef } from "react";
import { activeComposition } from "@/scene/motionState";
import { motion } from "@/scene/motionStore";
import { isSoftwareRenderer, rendererName } from "@/scene/renderer";

const SCALE = 0.2; // drawing-buffer pixels per CSS pixel
const FRAME_MS = 1000 / 30;

const VERTEX = `attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }`;

// Domain-warped fractal noise (two warp passes) shaped into drifting smoke, lit by a key light behind
// the car, an overhead softbox and the pointer. Output is opaque: graphite plus light, dithered.
const FRAGMENT = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 uRes;
uniform float uTime;
uniform vec2 uKey;
uniform vec2 uPointer;
uniform float uPointerAmt;
float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
  for (int i = 0; i < 5; i++) { v += a * noise(p); p = m * p; a *= 0.5; }
  return v;
}
void main() {
  vec2 uv = gl_FragCoord.xy / uRes;
  float aspect = uRes.x / uRes.y;
  vec2 p = vec2(uv.x * aspect, uv.y) * 2.2;
  float t = uTime * 0.035;
  vec2 q = vec2(fbm(p + vec2(0.0, -t)), fbm(p + vec2(5.2, 1.3) + vec2(t * 0.6, -t * 0.4)));
  vec2 r = vec2(fbm(p + 3.2 * q + vec2(1.7, 9.2) + 0.45 * t), fbm(p + 3.2 * q + vec2(8.3, 2.8) - 0.35 * t));
  float smoke = smoothstep(0.34, 0.95, fbm(p + 2.8 * r));
  float wisps = pow(1.0 - abs(2.0 * r.x - 1.0), 4.0); // thin filaments along the warp contours
  smoke *= 0.55 + 0.9 * wisps;
  vec2 a = vec2(aspect, 1.0);
  float key = exp(-pow(distance(uv * a, uKey * a) * 1.45, 2.0));
  float cursor = exp(-pow(distance(uv * a, uPointer * a) * 3.2, 2.0)) * uPointerAmt;
  float overhead = smoothstep(0.45, 1.1, uv.y) * 0.2;
  float floorHaze = smoothstep(0.55, 0.0, uv.y) * 0.25;
  float light = 0.12 + 1.25 * key + 0.8 * cursor + overhead + floorHaze;
  vec3 cool = vec3(0.50, 0.60, 0.82);
  vec3 warm = vec3(0.85, 0.78, 0.63);
  vec3 tint = mix(cool, warm, smoothstep(0.35, 0.85, r.y) * 0.55 + overhead * 0.4);
  vec3 base = vec3(0.047, 0.055, 0.067);
  vec3 col = base + tint * smoke * light * 0.13 + vec3(0.53, 0.65, 1.0) * cursor * 0.02;
  col += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
  gl_FragColor = vec4(col, 1.0);
}`;

// Static grain: SVG fractal noise, tiled (no animation, so no shimmer and no per-frame cost).
const GRAIN = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.6 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`;

function compile(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
}

export function Atmosphere() {
  const wrap = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = wrap.current;
    if (!canvas || !host) return;
    const gl = canvas.getContext("webgl", { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: "low-power" });
    if (!gl) {
      host.dataset.atmosphere = "off";
      return;
    }
    const vs = compile(gl, gl.VERTEX_SHADER, VERTEX);
    const fs = compile(gl, gl.FRAGMENT_SHADER, FRAGMENT);
    const program = gl.createProgram();
    if (!vs || !fs || !program) {
      host.dataset.atmosphere = "off";
      return;
    }
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      host.dataset.atmosphere = "off";
      return;
    }
    gl.useProgram(program);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW); // one full-screen triangle
    const loc = gl.getAttribLocation(program, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const u = {
      res: gl.getUniformLocation(program, "uRes"),
      time: gl.getUniformLocation(program, "uTime"),
      key: gl.getUniformLocation(program, "uKey"),
      pointer: gl.getUniformLocation(program, "uPointer"),
      pointerAmt: gl.getUniformLocation(program, "uPointerAmt"),
    };

    if (isSoftwareRenderer(rendererName(gl))) {
      host.dataset.atmosphere = "off";
      gl.getExtension("WEBGL_lose_context")?.loseContext();
      return;
    }
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    const key = { x: 0.7, y: 0.45 };
    const pointer = { x: 0.7, y: 0.5, tx: 0.7, ty: 0.5, amt: 0, target: 0 };
    let raf = 0;
    let last = 0;
    const start = performance.now();

    const resize = () => {
      const w = Math.max(1, Math.round(window.innerWidth * SCALE));
      const h = Math.max(1, Math.round(window.innerHeight * SCALE));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    const draw = (now: number) => {
      // Key light follows the car's screen anchor (the composition the camera is heading for).
      const comp = activeComposition(motion, window.innerWidth);
      key.x += (comp.anchor.x - key.x) * 0.08;
      key.y += (1 - comp.anchor.y - key.y) * 0.08;
      if (!finePointer.matches) {
        // No mouse: the light drifts slowly near the car on its own.
        const s = (now - start) / 1000;
        pointer.tx = key.x + Math.sin(s * 0.13) * 0.18;
        pointer.ty = key.y + Math.cos(s * 0.09) * 0.12;
        pointer.target = 0.6;
      }
      pointer.x += (pointer.tx - pointer.x) * 0.06;
      pointer.y += (pointer.ty - pointer.y) * 0.06;
      pointer.amt += (pointer.target - pointer.amt) * 0.05;
      gl.uniform2f(u.res, canvas.width, canvas.height);
      gl.uniform1f(u.time, ((now - start) / 1000) % 3600);
      gl.uniform2f(u.key, key.x, key.y);
      gl.uniform2f(u.pointer, pointer.x, pointer.y);
      gl.uniform1f(u.pointerAmt, pointer.amt);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };

    // Something of the haze is visible: always while choreography runs (sections are transparent),
    // otherwise only while the hero is on screen.
    const onScreen = () => document.documentElement.dataset.choreo === "on" || window.scrollY < window.innerHeight * 1.1;
    const animated = () => !reduce.matches && !document.hidden;

    const loop = (now: number) => {
      raf = 0;
      if (!animated()) return;
      raf = requestAnimationFrame(loop);
      if (now - last < FRAME_MS || !onScreen()) return;
      last = now;
      draw(now);
    };
    const still = () => {
      // One settled frame: key light and pointer at rest where they are.
      key.x = activeComposition(motion, window.innerWidth).anchor.x;
      key.y = 1 - activeComposition(motion, window.innerWidth).anchor.y;
      pointer.amt = 0;
      pointer.target = 0;
      draw(start + 40_000);
    };
    const sync = () => {
      host.dataset.atmosphere = animated() ? "animated" : "static";
      if (animated()) {
        if (!raf) raf = requestAnimationFrame(loop);
      } else {
        cancelAnimationFrame(raf);
        raf = 0;
        still();
      }
    };

    let resizeTimer = 0;
    const onResize = () => {
      resize();
      if (!animated()) {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(still, 120);
      }
    };
    const onPointer = (e: PointerEvent) => {
      if (e.pointerType !== "mouse" || !animated()) return;
      pointer.tx = e.clientX / window.innerWidth;
      pointer.ty = 1 - e.clientY / window.innerHeight;
      pointer.target = 1;
    };
    const onLeave = () => {
      pointer.target = 0;
    };

    resize();
    sync();
    window.addEventListener("resize", onResize, { passive: true });
    window.addEventListener("pointermove", onPointer, { passive: true });
    document.documentElement.addEventListener("pointerleave", onLeave);
    document.addEventListener("visibilitychange", sync);
    reduce.addEventListener("change", sync);
    canvas.style.opacity = "1";

    return () => {
      cancelAnimationFrame(raf);
      window.clearTimeout(resizeTimer);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("pointermove", onPointer);
      document.documentElement.removeEventListener("pointerleave", onLeave);
      document.removeEventListener("visibilitychange", sync);
      reduce.removeEventListener("change", sync);
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    };
  }, []);

  return (
    <div ref={wrap} aria-hidden="true" data-atmosphere="pending" className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* CSS haze: the whole effect without WebGL, and what shows before the first shader frame. */}
      <div className="absolute inset-0 bg-[radial-gradient(70%_60%_at_70%_45%,rgb(134_165_255/0.07),transparent_70%),radial-gradient(60%_40%_at_50%_0%,rgb(244_240_232/0.05),transparent_75%)]" />
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full opacity-0 transition-opacity duration-1000 motion-reduce:transition-none" />
      <div className="absolute inset-0 opacity-[0.07] mix-blend-overlay" style={{ backgroundImage: GRAIN }} />
    </div>
  );
}
