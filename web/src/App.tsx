// Owner: C. App shell: header with data label + data-as-of, routes for the five P0 screens.
import { NavLink, Route, Routes } from "react-router-dom";
import { getMeta } from "./api/client";
import { useApi } from "./api/useApi";
import { DATA_LABEL_TEXT, dateText } from "./format";
import IssuePage from "./pages/IssuePage";
import ReplayPage from "./pages/ReplayPage";
import ResultsPage from "./pages/ResultsPage";
import SelectorPage from "./pages/SelectorPage";
import VehiclePage from "./pages/VehiclePage";

function Header() {
  const [meta] = useApi(getMeta, []);
  return (
    <header className="site-header">
      <div className="header-row">
        <NavLink to="/" className="brand">
          Recall Radar
        </NavLink>
        <nav aria-label="Main">
          <NavLink to="/" end>
            Find a vehicle
          </NavLink>
          <NavLink to="/results">Results</NavLink>
        </nav>
        <p className="header-meta" data-testid="header-meta">
          {meta.state === "loading" && "Loading data status…"}
          {meta.state === "done" && meta.ok && (
            <>
              <span className={`badge badge-${meta.data.provenance.data_label}`}>
                {DATA_LABEL_TEXT[meta.data.provenance.data_label]}
              </span>{" "}
              Data as of{" "}
              {meta.data.provenance.data_as_of ? dateText(meta.data.provenance.data_as_of) : "not applicable (test data)"}
              {meta.source === "offline" && <span className="badge badge-offline">Offline demo data</span>}
            </>
          )}
          {meta.state === "done" && !meta.ok && "Data as of: see each page (data service offline)"}
        </p>
      </div>
    </header>
  );
}

function NotFound() {
  return (
    <section>
      <h1>Page not found</h1>
      <p>
        <NavLink to="/">Go to vehicle search</NavLink>
      </p>
    </section>
  );
}

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<SelectorPage />} />
          <Route path="/vehicle" element={<VehiclePage />} />
          <Route path="/issue/:groupId" element={<IssuePage />} />
          <Route path="/replay/:episodeId" element={<ReplayPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <p>
          An alert means a complaint pattern deserves a closer look. It is not a defect finding and not a recall
          forecast. Counts are distinct complaints from public NHTSA files. To check a specific car, use{" "}
          <a href="https://www.nhtsa.gov/recalls" target="_blank" rel="noopener noreferrer">
            NHTSA’s VIN lookup
          </a>
          .
        </p>
      </footer>
    </>
  );
}
