import { useState } from "react";

// Collapsible view of the retrieved knowledge-base chunks that grounded a
// question — this surfaces the RAG traceability (Context → Question) in the UI.
export default function ContextTrace({ chunks }) {
  const [open, setOpen] = useState(false);
  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="trace">
      <button
        type="button"
        className="trace__toggle"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? "▾" : "▸"} Grounded in {chunks.length} knowledge-base{" "}
        {chunks.length === 1 ? "chunk" : "chunks"}
      </button>
      {open && (
        <ul className="trace__list">
          {chunks.map((c, i) => (
            <li key={i} className="trace__item">
              <div className="trace__meta">
                <span className="trace__source">{c.source}</span>
                <span className="trace__score">
                  relevance {(c.score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="trace__snippet">{c.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
