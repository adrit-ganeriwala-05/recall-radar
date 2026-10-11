// Owner: C. Common frame for the HTML sections. In the `wide` layout each section is two columns: the
// content on the left and an empty right-hand "chapter stage" ([data-chapter-stage]) that the
// ScrollDirector measures, so the car is framed in empty space beside the text and never behind it.
// Sections are opaque sheets over the fixed scene except while the scroll choreography runs (`choreo`
// variant: <html data-choreo="on">, set by the ScrollDirector), where they let the car show through
// the stage column. Each opens with a fading hairline and a decorative section number (hidden from
// assistive technology; the heading carries the meaning). Gutters respect safe areas; text wraps
// rather than overflows at large text sizes.
import type { ReactNode } from "react";
import type { ChapterId } from "@/scene/motionState";

type Props = { id: string; title: string; chapter: ChapterId; children: ReactNode };

const NUMBER: Partial<Record<ChapterId, string>> = { overview: "01", explore: "02", record: "03", official: "04", report: "05", closing: "06" };

export function SectionShell({ id, title, chapter, children }: Props) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} data-chapter={chapter} className="relative bg-graphite choreo:bg-transparent">
      <div className="safe-px relative mx-auto grid max-w-[90rem] grid-cols-1 py-20 [overflow-wrap:anywhere] before:pointer-events-none before:absolute before:inset-x-5 before:top-0 before:h-px before:bg-[linear-gradient(90deg,transparent,var(--color-line-strong)_18%,var(--color-line-strong)_82%,transparent)] sm:py-28 wide:grid-cols-[minmax(0,58fr)_minmax(0,42fr)] wide:gap-x-10">
        <div data-reveal className="min-w-0">
          {NUMBER[chapter] && (
            <p aria-hidden="true" className="rr-eyebrow flex items-center gap-3">
              {NUMBER[chapter]}
              <span className="h-px w-10 bg-champagne/50" />
            </p>
          )}
          <h2 id={`${id}-title`} className="rr-display mt-5 text-[2.75rem] text-ink [overflow-wrap:anywhere] sm:text-6xl">
            {title}
          </h2>
          {children}
        </div>
        <div aria-hidden="true" data-chapter-stage={chapter} className="hidden wide:block" />
      </div>
    </section>
  );
}
