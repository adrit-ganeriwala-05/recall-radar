import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
// Typography (Space Grotesk + Manrope, self-hosted in public/fonts and preloaded by index.html) is
// declared and applied in styles.css.
import "./tailwind.css"; // chart components only (no global reset)
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
