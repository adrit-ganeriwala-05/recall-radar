// Owner: C. Authored presentation copy. No performance numbers are typed here (CLAUDE.md §1):
// the measured result is described in words and linked to the product's results page, which reads
// the exported evaluation JSON. Banned words are checked by scripts/check-copy.mjs.

/** PROJECT_SPEC §1: the promise, verbatim. */
export const PROMISE =
  "Recall Radar shows when owner complaints about the same vehicle and problem started growing unusually fast, and whether NHTSA later opened an investigation, using only data that was public at the time.";

export const HERO = {
  eyebrow: "The Automotive Observatory",
  titleLines: ["Your vehicle.", "The available evidence."],
  lede: "Explore reported problems, official recalls, and the records behind them.",
  primaryAction: "Explore vehicle records",
  secondaryAction: "See how it works",
  vehicleLabel: "Illustrative vehicle",
} as const;

export const NAV = {
  explore: "Explore",
  howItWorks: "How it works",
  evidence: "Evidence",
  openApp: "Open app",
} as const;

export const HOW_IT_WORKS = {
  title: "How it works",
  steps: [
    {
      title: "Complaints, in date order",
      body: "Public NHTSA complaints are counted as distinct complaints and replayed month by month, using only the records that were public at each date.",
    },
    {
      title: "Official records beside them",
      body: "NHTSA investigations and recall campaigns are shown next to the complaint history as later outcomes. They are never used to raise an alert.",
    },
    {
      title: "The measured result, stated plainly",
      body: "We tested whether a fast rise in complaints came before NHTSA opened an investigation. It did no better than chance, so Recall Radar is a way to inspect records, not a recall forecast.",
    },
  ],
  resultsLink: "See the measured results",
} as const;

export const FOOTER = {
  vinNote: "Recall campaigns apply to a model and model year, not to one specific car. To check a specific car, use NHTSA's recall lookup by VIN.",
  vinLink: "Check open recalls on NHTSA",
  dataNote: "Data: public NHTSA complaint, investigation and recall files. Counts are distinct complaints.",
  alertNote: "An alert means a complaint pattern deserves a closer look. It is not a defect finding and not a recall forecast.",
  modelCredit: {
    lead: "Illustrative vehicle: “Car Concept” by Eric Chadwick, © Darmstadt Graphics Group GmbH, from the Khronos glTF Sample Assets,",
    license: "CC BY 4.0",
    changes: "Modified: logos and licence plate removed, one paint variant kept, geometry compressed. Not a model-year representation; no endorsement implied.",
    sourceUrl: "https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept",
    licenseUrl: "https://creativecommons.org/licenses/by/4.0/",
  },
} as const;
