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

  const pad = (n) => String(n).padStart(2, "0");

  return (
    <div className="interview">
      <aside className="interview__side">
        <div className="counter">
          <span className="counter__num" aria-hidden="true">
            {pad(currentNumber)}
          </span>
          <span className="counter__of">
            <span className="sr-only">Question {currentNumber} </span>
            of {pad(total)} questions
          </span>
          <div className="progress">
            <div
              className="progress__bar"
              role="progressbar"
              aria-valuenow={progressPct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Interview progress"
            >
              <div
                className="progress__fill"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className="progress__meta">{progressPct}% complete</span>
          </div>
        </div>
        <ProfilePanel
          profile={session.profile}
          name={session.candidateName}
          variant="compact"
        />
        <ContextTrace chunks={question.context_chunks} variant="compact" />
      </aside>

      <section className="interview__main">
        <div className="question-card">
          <div className="question-card__tags">
            <span className="tag tag--topic">{question.topic}</span>
            <span className={`tag tag--diff tag--${question.difficulty}`}>
              {question.difficulty}
            </span>
          </div>
          <p className={`question-card__text${questionSizeClass(question.question)}`}>
            {question.question}
          </p>
          {question.rationale && (
            <p className="question-card__why">
              <strong>Why this question:</strong> {question.rationale}
            </p>
          )}

          <ContextTrace chunks={question.context_chunks} />
        </div>

        <form className="answer-card" onSubmit={handleSubmit}>
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
          {error && (
            <div className="alert" role="alert">
              {error}
            </div>
          )}
          <button
            className="btn btn--primary btn--bar btn--submit"
            type="submit"
            disabled={submitting}
          >
            <span>
              {submitting
                ? "Evaluating…"
                : currentNumber === total
                ? "Submit final answer"
                : "Submit & continue"}
            </span>
            {submitting && (
              <span className="btn__note">
                The next question adapts to what you just answered.
              </span>
            )}
          </button>
        </form>
      </section>
    </div>
  );
}

// Generated questions vary a lot in length; step the display size down for
// long ones so the answer box stays on screen.
function questionSizeClass(text = "") {
  if (text.length > 320) return " question-card__text--xlong";
  if (text.length > 180) return " question-card__text--long";
  return "";
}
