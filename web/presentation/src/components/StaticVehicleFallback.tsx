// Owner: C. Static illustrative vehicle used when the 3D scene cannot run (no WebGL, model failed to
// load or timed out, graphics context lost). Authored inline SVG of a generic car silhouette, nose
// toward screen-left like the 3D composition, drawn inside the measured hero stage. It is the
// fallback, not the finished 3D experience; the caption says so.
import type { Stage } from "@/scene/stage";

type Props = { reason: string; stage: Stage | null };

export function StaticVehicleFallback({ reason, stage }: Props) {
  if (!stage) return null;
  return (
    <div
      className="absolute flex flex-col items-center justify-center"
      style={{ left: stage.left, top: stage.top, width: stage.width, height: stage.height }}
    >
      <svg
        viewBox="0 0 640 240"
        className="h-auto max-h-[78%] w-[92%]"
        role="presentation"
        style={{ transform: "scaleX(-1)" }}
      >
        <defs>
          <linearGradient id="rr-pearl" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#eceae5" />
            <stop offset="0.55" stopColor="#bfc2c6" />
            <stop offset="1" stopColor="#8e9297" />
          </linearGradient>
          <radialGradient id="rr-floor" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#000" stopOpacity="0.55" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
        </defs>
        <ellipse cx="322" cy="214" rx="300" ry="20" fill="url(#rr-floor)" />
        <path
          d="M40 170 C40 150 55 140 80 136 L160 126 C190 96 230 72 290 66 L400 64 C440 64 470 80 500 104 L560 116 C590 122 606 138 606 158 L606 172 C606 178 600 182 594 182 L546 182 A46 46 0 0 0 454 182 L206 182 A46 46 0 0 0 114 182 L52 182 C45 182 40 177 40 170 Z"
          fill="url(#rr-pearl)"
          stroke="#f5f2eb"
          strokeOpacity="0.25"
        />
        <path d="M178 128 C204 100 236 84 286 80 L330 79 L330 126 Z" fill="#1c2024" />
        <path d="M342 79 L398 79 C430 80 456 94 478 116 L342 120 Z" fill="#1c2024" />
        {[160, 500].map((cx) => (
          <g key={cx}>
            <circle cx={cx} cy="182" r="38" fill="#111315" />
            <circle cx={cx} cy="182" r="22" fill="#5d6268" stroke="#aeb6be" strokeOpacity="0.4" />
          </g>
        ))}
      </svg>
      <p className="mt-1 px-2 text-center text-xs text-muted">Static illustration — 3D view unavailable ({reason})</p>
    </div>
  );
}
