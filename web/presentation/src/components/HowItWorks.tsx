// Owner: C. Plain explanation of the product and its measured limits. No numbers are typed here:
// the results link opens the product page that renders the exported evaluation JSON. Part of the
// "overview" chapter: the car keeps the hero's front three-quarter, framed in this section's stage.
import { HOW_IT_WORKS, PROMISE } from "@/content/copy";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";
import { SectionShell } from "./sections/SectionShell";

export function HowItWorks() {
  return (
    <SectionShell id={SECTION_IDS.howItWorks} title={HOW_IT_WORKS.title} chapter="overview">
      <p className="mt-6 max-w-3xl text-lg leading-relaxed text-muted">{PROMISE}</p>
      {/* auto-fit with a min(100%, …) floor: columns appear only where they fit, and at large text sizes
          the cards wrap their text instead of pushing the page sideways. */}
      <ol className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(min(100%,15rem),1fr))] gap-6">
        {HOW_IT_WORKS.steps.map((step, i) => (
          <li key={step.title} className="rr-card min-w-0 p-6 sm:p-7">
            <p className="rr-eyebrow">Step {i + 1}</p>
            <h3 className="mt-4 text-xl font-medium tracking-tight">{step.title}</h3>
            <p className="mt-3 leading-relaxed text-muted">{step.body}</p>
          </li>
        ))}
      </ol>
      <p className="mt-10">
        <SmartLink
          to={DESTINATIONS.results}
          className="inline-flex min-h-11 items-center rounded text-base rr-link"
        >
          {HOW_IT_WORKS.resultsLink}
        </SmartLink>
      </p>
    </SectionShell>
  );
}
