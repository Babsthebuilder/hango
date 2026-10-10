import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="boot-shell">
      <div className="pitch-mark" aria-hidden="true">
        <span />
      </div>
      <section aria-labelledby="hango-title">
        <p className="eyebrow">Football relational intelligence</p>
        <h1 id="hango-title">HANGO</h1>
        <p className="tagline">Reveal the geometry behind the goal.</p>
        <p className="phase">Phase 1 foundation</p>
      </section>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("HANGO root element was not found");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
