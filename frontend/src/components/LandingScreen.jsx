// First thing the user sees: a calm, brief explanation of what the product does
// and a single call-to-action into the screening flow.

const FEATURES = [
  {
    title: "Resume-aware",
    body: "We parse your resume to extract real skills, technologies and domains — then target the interview at what you actually know.",
    icon: (
      <path d="M14 3v4a1 1 0 0 0 1 1h4M5 3h9l5 5v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM8 13h8M8 17h5" />
    ),
  },
  {
    title: "Grounded in a knowledge base",
    body: "Every question is retrieved from an authoritative textbook via RAG — no generic trivia — and each one is fully traceable to its source.",
    icon: (
      <path d="M4 5a2 2 0 0 1 2-2h9l5 5v9M4 5v14a2 2 0 0 0 2 2h9M4 5h6M8 12h8M8 16h5" />
    ),
  },
  {
    title: "Adaptive & evaluated",
    body: "Questions adapt to your previous answers and rise in difficulty. At the end you get a structured summary with strengths and gaps.",
    icon: <path d="M3 17l5-5 4 4 8-8M21 8v5M21 8h-5" />,
  },
];

const STEPS = [
  "Upload your resume and choose a target role",
  "We retrieve role-specific context and generate tailored questions",
  "Answer in an interactive interview and receive a structured assessment",
];

export default function LandingScreen({ onStart }) {
  return (
    <div className="landing">
      <section className="landing__hero">
        <span className="landing__eyebrow">AI-powered screening</span>
        <h2 className="landing__title">
          Technical interviews that actually understand the candidate
        </h2>
        <p className="landing__lead">
          Upload a resume, pick a role, and this system runs a structured
          technical interview — dynamically generating questions grounded in a
          role-specific knowledge base and tailored to your background. It adapts
          as you answer, then gives a clear, evidence-based summary.
        </p>
        <div className="landing__cta">
          <button className="btn btn--primary landing__ctabtn" onClick={onStart}>
            Start interview screening
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>
          <span className="landing__ctanote">Takes about 5 questions · free to run</span>
        </div>
      </section>

      <section className="landing__features">
        {FEATURES.map((f) => (
          <div className="card feature" key={f.title}>
            <span className="feature__icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                {f.icon}
              </svg>
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
              <span className="howstep__num">{i + 1}</span>
              <span className="howstep__text">{s}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
