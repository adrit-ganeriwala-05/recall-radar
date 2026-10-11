// Owner: C. The presentation is a static export served from web/dist/observatory/. Both production
// servers (Caddy try_files, FastAPI) serve /observatory/index.html as a file but send the bare
// /observatory and /observatory/ URLs to this SPA, so this route forwards exactly those two to the
// file. /observatory/index.html itself never reaches this route (it is a different path), so a missing
// export shows the normal "Page not found" instead of a redirect loop.
import { useEffect } from "react";

export const OBSERVATORY_FILE = "/observatory/index.html";

type Props = { navigate?: (url: string) => void };

export default function ObservatoryRedirect({ navigate = (url) => window.location.replace(url) }: Props) {
  useEffect(() => {
    navigate(OBSERVATORY_FILE);
  }, [navigate]);
  return (
    <section>
      <h1>Opening the presentation…</h1>
      <p>
        If nothing happens, <a href={OBSERVATORY_FILE}>open the presentation</a>.
      </p>
    </section>
  );
}
