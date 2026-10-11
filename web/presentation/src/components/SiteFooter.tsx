// Owner: C. Closing notes required on every Recall Radar surface: model-level campaigns never imply
// one car's status, and NHTSA's VIN lookup is always offered (CLAUDE.md §1).
import { FOOTER, HERO } from "@/content/copy";
import { DESTINATIONS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

export function SiteFooter() {
  return (
    <footer className="relative bg-graphite">
      <div aria-hidden="true" className="rr-hairline absolute inset-x-0 top-0" />
      <div className="safe-px mx-auto grid max-w-[90rem] gap-6 py-14 text-sm leading-relaxed text-muted [padding-bottom:max(3.5rem,env(safe-area-inset-bottom))] md:grid-cols-2">
        <p className="rr-eyebrow md:col-span-2">Recall Radar · {HERO.eyebrow}</p>
        <p>
          {FOOTER.vinNote}{" "}
          <SmartLink to={DESTINATIONS.nhtsaRecalls} className="rr-link">
            {FOOTER.vinLink}
          </SmartLink>
        </p>
        <div className="space-y-2">
          <p>{FOOTER.alertNote}</p>
          <p>{FOOTER.dataNote}</p>
        </div>
        <p className="text-faint md:col-span-2">
          {FOOTER.modelCredit.lead}{" "}
          <a href={FOOTER.modelCredit.licenseUrl} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 hover:text-ink">
            {FOOTER.modelCredit.license}
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
          . {FOOTER.modelCredit.changes}{" "}
          <a href={FOOTER.modelCredit.sourceUrl} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 hover:text-ink">
            Source
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
        </p>
      </div>
    </footer>
  );
}
