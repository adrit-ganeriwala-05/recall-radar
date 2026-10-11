// Owner: C. Closing notes required on every Recall Radar surface: model-level campaigns never imply
// one car's status, and NHTSA's VIN lookup is always offered (CLAUDE.md §1).
import { FOOTER } from "@/content/copy";
import { DESTINATIONS } from "@/content/destinations";
import { SmartLink } from "./SmartLink";

export function SiteFooter() {
  return (
    <footer className="relative border-t border-line bg-graphite">
      <div className="mx-auto grid max-w-[90rem] gap-4 px-5 py-12 text-sm leading-relaxed text-muted sm:px-8 md:grid-cols-2">
        <p>
          {FOOTER.vinNote}{" "}
          <SmartLink to={DESTINATIONS.nhtsaRecalls} className="text-cobalt underline underline-offset-4 hover:text-ink">
            {FOOTER.vinLink}
          </SmartLink>
        </p>
        <div className="space-y-2">
          <p>{FOOTER.alertNote}</p>
          <p>{FOOTER.dataNote}</p>
        </div>
        <p className="md:col-span-2">
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
