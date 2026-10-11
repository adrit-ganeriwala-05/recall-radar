// Owner: C. The presentation page. Server Component: all Phase 1 content is static HTML, rendered
// at build time, readable and navigable without JavaScript or WebGL.
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { PresentationRoot } from "@/components/PresentationRoot";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function ObservatoryPage() {
  return (
    <PresentationRoot header={<SiteHeader />}>
      <main>
        <Hero />
        <HowItWorks />
      </main>
      <SiteFooter />
    </PresentationRoot>
  );
}
