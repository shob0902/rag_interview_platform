import { useState } from "react";
import LandingScreen from "./components/LandingScreen.jsx";
import SetupScreen from "./components/SetupScreen.jsx";
import InterviewScreen from "./components/InterviewScreen.jsx";
import SummaryScreen from "./components/SummaryScreen.jsx";
import Stepper from "./components/Stepper.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";
import { useTheme } from "./useTheme.js";

// The app is a small state machine. "landing" is the intro view shown first;
// the three interview stages drive the stepper. Keeping stage + shared session
// data in one place keeps the flow easy to follow and state consistent.
const STAGES = ["setup", "interview", "summary"];

export default function App() {
  const [stage, setStage] = useState("landing");
  const [session, setSession] = useState(null); // { sessionId, role, profile, totalQuestions }
  const [firstQuestion, setFirstQuestion] = useState(null);
  const { theme, toggle } = useTheme();

  const onLanding = stage === "landing";

  function handleStarted(startResponse) {
    setSession({
      sessionId: startResponse.session_id,
      role: startResponse.role,
      candidateName: startResponse.candidate_name,
      profile: startResponse.resume_profile,
      totalQuestions: startResponse.total_questions,
    });
    setFirstQuestion(startResponse.question);
    setStage("interview");
  }

  function handleFinished() {
    setStage("summary");
  }

  function handleRestart() {
    setSession(null);
    setFirstQuestion(null);
    setStage("landing");
  }

  return (
    <div className="app">
      <header className="app__header">
        <button
          type="button"
          className="app__brand app__brand--btn"
          onClick={() => setStage("landing")}
          aria-label="Back to home"
        >
          <span className="app__logo" aria-hidden="true" />
          <h1 className="app__brandname">Screening.</h1>
        </button>
        <div className="app__headerright">
          {!onLanding && <Stepper stages={STAGES} current={stage} />}
          <div className="app__togglecell">
            <ThemeToggle theme={theme} onToggle={toggle} />
          </div>
        </div>
      </header>

      <main className="app__main" key={stage}>
        {stage === "landing" && (
          <LandingScreen onStart={() => setStage("setup")} />
        )}
        {stage === "setup" && <SetupScreen onStarted={handleStarted} />}
        {stage === "interview" && (
          <InterviewScreen
            session={session}
            firstQuestion={firstQuestion}
            onFinished={handleFinished}
          />
        )}
        {stage === "summary" && (
          <SummaryScreen session={session} onRestart={handleRestart} />
        )}
      </main>

      <footer className="app__footer">
        Context → Question → Answer → Storage · grounded in a role-specific
        knowledge base
      </footer>
    </div>
  );
}
