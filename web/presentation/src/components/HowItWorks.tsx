// Owner: C. Plain explanation of the product and its measured limits. No numbers are typed here:
// the results link opens the product page that renders the exported evaluation JSON.
import { HOW_IT_WORKS, PROMISE } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

export function HowItWorks() {
  return (
    <section
      id={SECTION_IDS.howItWorks}
      aria-labelledby="how-title"
      className="mx-auto max-w-[90rem] border-t border-line px-5 py-24 sm:px-8"
    >
      <h2 id="how-title" className="text-4xl font-medium tracking-[-0.02em] sm:text-5xl">
        {HOW_IT_WORKS.title}
      </h2>
      <p className="mt-6 max-w-3xl text-lg leading-relaxed text-muted">{PROMISE}</p>
      <ol className="mt-12 grid gap-6 md:grid-cols-3">
        {HOW_IT_WORKS.steps.map((step, i) => (
          <li key={step.title} className="rounded-xl border border-line bg-surface p-6">
            <p className="text-sm font-medium text-cobalt">Step {i + 1}</p>
            <h3 className="mt-2 text-xl font-medium">{step.title}</h3>
            <p className="mt-3 leading-relaxed text-muted">{step.body}</p>
          </li>
        ))}
      </ol>
      <p className="mt-10">
        <SmartLink
          to={DESTINATIONS.results}
          className="inline-flex min-h-11 items-center rounded text-base text-cobalt underline underline-offset-4 hover:text-ink"
        >
          {HOW_IT_WORKS.resultsLink}
        </SmartLink>
      </p>
    </section>
  );
}
