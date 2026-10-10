// Owner: C. Shown on every vehicle render: campaigns are model-level, never a car's status.
export const VIN_LOOKUP_URL = "https://www.nhtsa.gov/recalls";

export function VinBox({ url = VIN_LOOKUP_URL }: { url?: string }) {
  return (
    <aside className="vin-box" aria-label="Check a specific car">
      <h3>Check your specific car</h3>
      <p>
        Recall campaigns listed here apply to this model and model year. They do not tell you whether a
        particular car is affected or has already been repaired.
      </p>
      <p>
        <a href={url} target="_blank" rel="noopener noreferrer" data-testid="vin-link">
          Look up a VIN at NHTSA (nhtsa.gov/recalls)
        </a>
      </p>
    </aside>
  );
}
