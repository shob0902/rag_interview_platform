import { useState } from "react";
import { submitAnswer } from "../api.js";
import ProfilePanel from "./ProfilePanel.jsx";
import ContextTrace from "./ContextTrace.jsx";

// Drives the interactive interview: shows the current question, collects an
// answer, and advances to the next question (or the summary) on submit.
export default function InterviewScreen({ session, firstQuestion, onFinished }) {
  const [question, setQuestion] = useState(firstQuestion);
  const [answer, setAnswer] = useState("");
  const [answeredCount, setAnsweredCount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const total = session.totalQuestions;
  const currentNumber = answeredCount + 1;
  const progressPct = Math.round((answeredCount / total) * 100);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!answer.trim()) return setError("Please enter an answer.");
    setError("");
    setSubmitting(true);
    try {
      const res = await submitAnswer(session.sessionId, answer.trim());
      setAnsweredCount(res.questions_answered);
      setAnswer("");
      if (res.status === "completed") {
        onFinished();
      } else {
        setQuestion(res.next_question);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="interview">
      <aside className="interview__side">
        <ProfilePanel profile={session.profile} name={session.candidateName} />
      </aside>

      <section className="interview__main">
        <div className="progress">
          <div className="progress__meta">
            <span>
              Question {currentNumber} of {total}
            </span>
            <span className="muted">{progressPct}% complete</span>
          </div>
          <div className="progress__bar">
            <div
              className="progress__fill"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="card question-card">
          <div className="question-card__tags">
            <span className="tag tag--topic">{question.topic}</span>
            <span className={`tag tag--diff tag--${question.difficulty}`}>
              {question.difficulty}
            </span>
          </div>
          <p className="question-card__text">{question.question}</p>
          {question.rationale && (
            <p className="question-card__why">
              <strong>Why this question:</strong> {question.rationale}
            </p>
          )}

          <ContextTrace chunks={question.context_chunks} />
        </div>

        <form className="card answer-card" onSubmit={handleSubmit}>
          <label className="field">
            <span>Your answer</span>
            <textarea
              rows={7}
              value={answer}
              placeholder="Type your answer…"
              onChange={(e) => setAnswer(e.target.value)}
              disabled={submitting}
              autoFocus
            />
          </label>
          {error && <div className="alert">{error}</div>}
          <button
            className="btn btn--primary"
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? "Evaluating & preparing next…"
              : currentNumber === total
              ? "Submit final answer"
              : "Submit & continue"}
          </button>
          {submitting && (
            <p className="muted small">
              The next question adapts to what you just answered.
            </p>
          )}
        </form>
      </section>
    </div>
  );
}
