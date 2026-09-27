import { useEffect, useState } from "react";
import { getSession } from "../api.js";
import ProfilePanel from "./ProfilePanel.jsx";
import ContextTrace from "./ContextTrace.jsx";

// Final output: structured summary + insights + full traceable transcript.
export default function SummaryScreen({ session, onRestart }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getSession(session.sessionId)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [session.sessionId]);

  if (error)
    return (
      <div className="alert" role="alert">
        {error}
      </div>
    );
  if (!data) return <div className="card">Loading summary…</div>;

  const insights = data.insights;

  return (
    <div className="summary">
      <div className="summary__grid">
        <aside className="summary__side">
          <ProfilePanel profile={data.resume_profile} name={data.candidate_name} />
        </aside>

        <section className="summary__main">
          <div className="summary__head">
            <h2>Interview summary</h2>
            <p className="muted">
              {data.candidate_name} · {roleLabel(data.role)} ·{" "}
              {data.questions.length} questions
            </p>
          </div>

          {insights ? (
            <div className="insights">
              {insights.score !== null && insights.score !== undefined && (
                <div className="scorecard">
                  <div className="scorecard__score">{insights.score}</div>
                  <div className="scorecard__label">
                    <span className="scorecard__max">/ 100</span>
                    <strong>{insights.recommendation}</strong>
                  </div>
                </div>
              )}
              <p className="insights__assessment">
                {insights.overall_assessment}
              </p>
              <div className="insights__cols">
                <ListBlock
                  title="Strengths"
                  items={insights.strengths}
                  variant="ok"
                />
                <ListBlock
                  title="Gaps"
                  items={insights.areas_to_improve}
                  variant="warn"
                />
              </div>
            </div>
          ) : (
            <p className="muted insights__empty">No insights available.</p>
          )}

          <h3 className="transcript__heading">Full transcript</h3>
          {data.questions.map((q, i) => (
            <div key={q.id} className="transcript__item">
              <span className="transcript__num">Q{i + 1}.</span>
              <div className="transcript__body">
                <div className="question-card__tags">
                  <span className="tag tag--topic">{q.topic}</span>
                  <span className={`tag tag--diff tag--${q.difficulty}`}>
                    {q.difficulty}
                  </span>
                </div>
                <p className="transcript__q">{q.question}</p>
                <p className="transcript__a">
                  <strong>Answer</strong>
                  {q.answer || <em className="muted">Not answered</em>}
                </p>
                {q.rationale && (
                  <p className="muted small">
                    <strong>Why asked:</strong> {q.rationale}
                  </p>
                )}
                <ContextTrace chunks={q.context_chunks} />
              </div>
            </div>
          ))}

          <button className="btn btn--bar" onClick={onRestart}>
            Start a new interview
          </button>
        </section>
      </div>
    </div>
  );
}

function ListBlock({ title, items, variant }) {
  if (!items || items.length === 0) return null;
  return (
    <div className={`listblock listblock--${variant}`}>
      <h4>{title}</h4>
      <ul>
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </div>
  );
}

function roleLabel(id) {
  return id
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}
