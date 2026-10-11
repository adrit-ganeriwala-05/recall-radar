// Owner: C. The presentation page. Server Component: all text is static HTML rendered at build time,
// readable and navigable without JavaScript or WebGL; the 3D scene mounts client-side behind it.
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { PresentationRoot } from "@/components/PresentationRoot";
import { SceneLayerLoader } from "@/components/SceneLayerLoader";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

export default function ObservatoryPage() {
  return (
    <PresentationRoot scene={<SceneLayerLoader />} header={<SiteHeader />}>
      <main>
        <Hero />
        <HowItWorks />
      </main>
      <SiteFooter />
    </PresentationRoot>
  );
}
