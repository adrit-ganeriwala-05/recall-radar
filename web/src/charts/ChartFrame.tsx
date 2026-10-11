// Owner: C. The frame around every chart: visible title, short description and accessible name; a
// Chart / Table switch (the table is the accessible data); stable-height loading, empty and error states;
// a text summary beneath. The chart body mounts the first time it scrolls into view, so its Bklit entrance
// animation runs once, when it is first seen, and never again on scroll. Light module: no chart library.
import { motion } from "motion/react";
import { useEffect, useId, useRef, useState, type ReactNode, type RefObject } from "react";
import { sectionViewport, stateFade, useMotionPresets } from "../ui/motion";

export type ChartState =
  | { kind: "loading" }
  | { kind: "empty"; message: string }
  | { kind: "error"; message: string; onRetry?: () => void }
  | { kind: "ready" };

/** Reserved plot area: the same box for skeleton and chart, so nothing shifts when the chart arrives. */
export function ChartSkeleton({ label }: { label: string }) {
  return (
    <div className="rr-chart-plot rr-chart-skeleton" role="status" aria-live="polite">
      <span className="visually-hidden">Loading {label}…</span>
    </div>
  );
}

function useFirstVisible<T extends Element>(): [RefObject<T | null>, boolean] {
  const ref = useRef<T>(null);
  const [visible, setVisible] = useState(() => typeof IntersectionObserver === "undefined");
  useEffect(() => {
    if (visible || !ref.current) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.1 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, [visible]);
  return [ref, visible];
}

interface Props {
  title: string;
  description: string;
  state: ChartState;
  /** The chart (a lazily loaded Bklit chart component). */
  children: ReactNode;
  /** Accessible data table for the values that matter. */
  table?: ReactNode;
  /** One or two sentences beneath the chart stating what it shows, from the same data. */
  summary?: ReactNode;
  /** Legend / marker list shown under the chart in chart view. */
  legend?: ReactNode;
  initialView?: "chart" | "table";
  testId?: string;
}

export function ChartFrame({ title, description, state, children, table, summary, legend, initialView = "chart", testId }: Props) {
  const mp = useMotionPresets();
  const [view, setView] = useState(initialView);
  const titleId = useId();
  const descId = useId();
  const [bodyRef, visible] = useFirstVisible<HTMLDivElement>();

  return (
    <motion.figure
      className="rr-chart"
      aria-labelledby={titleId}
      aria-describedby={descId}
      data-testid={testId}
      variants={mp.section}
      initial="hidden"
      whileInView="shown"
      viewport={sectionViewport}
    >
      <figcaption className="rr-chart-head">
        <div className="rr-chart-heading">
          <p id={titleId} className="chart-title">
            {title}
          </p>
          <p id={descId} className="rr-chart-desc">
            {description}
          </p>
        </div>
        {state.kind === "ready" && table && (
          <span className="view-toggle" role="group" aria-label={`${title}: view`}>
            <motion.button type="button" aria-pressed={view === "chart"} onClick={() => setView("chart")} {...mp.buttonTap}>
              Chart
            </motion.button>
            <motion.button type="button" aria-pressed={view === "table"} onClick={() => setView("table")} {...mp.buttonTap}>
              Table
            </motion.button>
          </span>
        )}
      </figcaption>

      <div ref={bodyRef}>
        {state.kind === "loading" && <ChartSkeleton label={title} />}
        {state.kind === "empty" && (
          <motion.p className="state state-empty rr-chart-state" role="status" {...stateFade}>
            {state.message}
          </motion.p>
        )}
        {state.kind === "error" && (
          <motion.div className="state state-error rr-chart-state" role="alert" {...stateFade}>
            <p>{state.message}</p>
            {state.onRetry && (
              <motion.button type="button" onClick={state.onRetry} {...mp.buttonTap}>
                Try again
              </motion.button>
            )}
          </motion.div>
        )}
        {state.kind === "ready" &&
          (view === "table" && table ? (
            <motion.div className="table-scroll" {...stateFade}>
              {table}
            </motion.div>
          ) : visible ? (
            <>
              {children}
              {legend}
            </>
          ) : (
            <ChartSkeleton label={title} />
          ))}
      </div>
      {state.kind === "ready" && summary && <p className="rr-chart-summary">{summary}</p>}
    </motion.figure>
  );
}
