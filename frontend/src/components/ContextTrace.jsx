import { useState } from "react";

const pct = (score) => `${(score * 100).toFixed(0)}%`;

// View of the retrieved knowledge-base chunks that grounded a question — this
// surfaces the RAG traceability (Context → Question) in the UI.
// variant="compact" renders a static source + relevance list for the sidebar;
// the default is a collapsible list including the passage snippets.
export default function ContextTrace({ chunks, variant = "full" }) {
  const [open, setOpen] = useState(false);
  if (!chunks || chunks.length === 0) return null;

  if (variant === "compact") {
    return (
      <div className="sources">
        <h4>Sources</h4>
        <ul className="sources__list">
          {chunks.map((c, i) => (
            <li key={i} className="sources__item">
              <span className="sources__name" title={c.source}>
                {c.source}
              </span>
              <span className="sources__score" aria-label={`relevance ${pct(c.score)}`}>
                {pct(c.score)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="trace">
      <button
        type="button"
        className="trace__toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {open ? "Hide" : "View"} {chunks.length}{" "}
        {chunks.length === 1 ? "passage" : "passages"} {open ? "−" : "+"}
      </button>
      {open && (
        <ul className="trace__list">
          {chunks.map((c, i) => (
            <li key={i} className="trace__item">
              <div className="trace__meta">
                <span className="trace__source">{c.source}</span>
                <span className="trace__score">relevance {pct(c.score)}</span>
              </div>
              <p className="trace__snippet">{c.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
