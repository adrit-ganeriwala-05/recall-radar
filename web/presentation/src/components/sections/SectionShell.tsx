// Owner: C. Common frame for the HTML sections: opaque sheet over the fixed scene, consistent gutters
// (safe areas included), comfortable reading width on ultrawide screens, one h2 per section, and
// text that wraps rather than overflows at large text sizes.
import type { ReactNode } from "react";

type Props = { id: string; title: string; children: ReactNode };

export function SectionShell({ id, title, children }: Props) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="relative bg-graphite">
      {/* overflow-wrap is inherited: at large text sizes a long word breaks instead of overflowing a card. */}
      <div className="safe-px mx-auto max-w-[90rem] border-t border-line py-16 [overflow-wrap:anywhere] sm:py-24">
        <h2 id={`${id}-title`} className="text-3xl font-medium tracking-[-0.02em] [overflow-wrap:anywhere] sm:text-5xl">
          {title}
        </h2>
        {children}
      </div>
    </section>
  );
}
