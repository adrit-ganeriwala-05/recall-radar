// Owner: C. The presentation page. Server Component: all text is static HTML rendered at build time,
// readable and navigable without JavaScript or WebGL; the 3D scene mounts client-side behind it, and
// the data sections load the published example from the product API in the browser. The release
// ledger (docs/LEDGER.md) is read here at build time and decides which features may be offered.
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { PresentationRoot } from "@/components/PresentationRoot";
import { SceneLayerLoader } from "@/components/SceneLayerLoader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { ContinueSection } from "@/components/sections/ContinueSection";
import { EvidenceSection } from "@/components/sections/EvidenceSection";
import { ExploreSection } from "@/components/sections/ExploreSection";
import { OfficialSection } from "@/components/sections/OfficialSection";
import { RecordSection } from "@/components/sections/RecordSection";
import { readLedger } from "@/content/ledger";
import { FeaturedVehicleProvider } from "@/data/FeaturedVehicle";

export default function ObservatoryPage() {
  const ledger = readLedger();
  return (
    <PresentationRoot scene={<SceneLayerLoader />} header={<SiteHeader />}>
      <main id="main" tabIndex={-1} className="outline-none">
        <Hero />
        <HowItWorks />
        <FeaturedVehicleProvider>
          <ExploreSection />
          <RecordSection />
          <OfficialSection f1={ledger.entries.F1} />
          <EvidenceSection f8={ledger.entries.F8} />
        </FeaturedVehicleProvider>
        <ContinueSection ledger={ledger} />
      </main>
      <SiteFooter />
    </PresentationRoot>
  );
}
