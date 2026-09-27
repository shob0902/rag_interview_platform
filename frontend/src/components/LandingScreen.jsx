// First thing the user sees: a brief explanation of what the product does and
// a single call-to-action into the screening flow.

const FEATURES = [
  {
    title: "Resume-aware",
    body: "We parse your resume to extract real skills, technologies and domains — then target the interview at what you actually know.",
  },
  {
    title: "Grounded in a knowledge base",
    body: "Every question is retrieved from an authoritative textbook via RAG — no generic trivia — and each one is fully traceable to its source.",
  },
  {
    title: "Adaptive & evaluated",
    body: "Questions adapt to your previous answers and rise in difficulty. At the end you get a structured summary with strengths and gaps.",
  },
];

const STEPS = [
  "Upload your resume and choose a target role",
  "We retrieve role-specific context and generate tailored questions",
  "Answer in an interactive interview and receive a structured assessment",
];

const pad = (n) => String(n).padStart(2, "0");

export default function LandingScreen({ onStart }) {
  return (
    <div className="landing">
      <section className="landing__hero">
        <div className="landing__heroinner">
          <span className="landing__eyebrow">AI-powered screening</span>
          <h2 className="landing__title">
            Technical interviews that actually understand the candidate
          </h2>
          <p className="landing__lead">
            Upload a resume, pick a role, and this system runs a structured
            technical interview — dynamically generating questions grounded in a
            role-specific knowledge base and tailored to your background. It
            adapts as you answer, then gives a clear, evidence-based summary.
          </p>
          <span className="landing__ctanote">
            Takes about 5 questions · free to run
          </span>
        </div>
        <button
          className="btn btn--primary btn--bar landing__ctabtn"
          onClick={onStart}
        >
          Start interview screening
        </button>
      </section>

      <section className="landing__features">
        {FEATURES.map((f, i) => (
          <div className="feature" key={f.title}>
            <span className="feature__num" aria-hidden="true">
              {pad(i + 1)}
            </span>
            <h3 className="feature__title">{f.title}</h3>
            <p className="feature__body">{f.body}</p>
          </div>
        ))}
      </section>

      <section className="landing__how">
        <h4 className="landing__howtitle">How it works</h4>
        <ol className="howsteps">
          {STEPS.map((s, i) => (
            <li className="howstep" key={i}>
              <span className="howstep__num" aria-hidden="true">
                {pad(i + 1)}
              </span>
              <span className="howstep__text">{s}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
