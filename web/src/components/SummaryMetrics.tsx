// Owner: C. Single values (counts, snapshot date) as accessible metric cards, not charts. Cards enter
// with the section stagger and lift 2 px on hover; the measured value is in the DOM from the first
// render (never counted up from zero), so no misleading intermediate number is ever shown.
import { motion } from "motion/react";
import { sectionViewport, useMotionPresets } from "../ui/motion";

export interface SummaryMetric {
  label: string;
  value: string;
  help?: string;
  testId?: string;
}

export function SummaryMetrics({ label, items }: { label: string; items: SummaryMetric[] }) {
  const mp = useMotionPresets();
  return (
    <motion.dl className="summary-metrics" aria-label={label} variants={mp.section} initial="hidden" whileInView="shown" viewport={sectionViewport}>
      {items.map((m) => (
        <motion.div key={m.label} className="metric" data-testid={m.testId} variants={mp.sectionChild} {...mp.cardHover}>
          <dt className="metric-label">{m.label}</dt>
          <dd className="metric-value">{m.value}</dd>
          {m.help && <dd className="metric-help">{m.help}</dd>}
        </motion.div>
      ))}
    </motion.dl>
  );
}
