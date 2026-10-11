// Owner: C. Static illustrative vehicle used when the 3D scene cannot run (no WebGL, model failed to
// load, graphics context lost). Authored inline SVG of a generic hatchback silhouette, nose toward
// screen-left like the 3D composition. It is the fallback, not the finished 3D experience; the
// caption says so. Positioned where the 3D car would sit (right column wide, above the copy narrow).

type Props = { reason: string };

export function StaticVehicleFallback({ reason }: Props) {
  return (
    <div className="absolute inset-x-[7%] top-[13%] lg:inset-x-auto lg:left-[44%] lg:right-[3%] lg:top-[34%]">
      <svg viewBox="0 0 640 240" className="w-full" role="presentation" style={{ transform: "scaleX(-1)" }}>
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
      <p className="mt-3 text-center text-xs text-muted">Static illustration — 3D view unavailable ({reason})</p>
    </div>
  );
}
