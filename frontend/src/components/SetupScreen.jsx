import { useEffect, useState } from "react";
import { getRoles, startInterview } from "../api.js";

// Candidate entry: choose a role, provide a resume (upload or paste), start.
export default function SetupScreen({ onStarted }) {
  const [roles, setRoles] = useState([]);
  const [role, setRole] = useState("");
  const [candidateName, setCandidateName] = useState("");
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [mode, setMode] = useState("upload"); // "upload" | "paste"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getRoles()
      .then((data) => {
        setRoles(data);
        if (data.length) setRole(data[0].id);
      })
      .catch((e) => setError(`Could not load roles: ${e.message}`));
  }, []);

  const selectedRole = roles.find((r) => r.id === role);
  const kbReady = selectedRole && selectedRole.document_count > 0;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!role) return setError("Please select a role.");
    if (mode === "upload" && !file) return setError("Please upload a resume file.");
    if (mode === "paste" && !resumeText.trim())
      return setError("Please paste your resume text.");

    setLoading(true);
    try {
      const res = await startInterview({
        role,
        candidateName,
        file: mode === "upload" ? file : null,
        resumeText: mode === "paste" ? resumeText : null,
      });
      onStarted(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="setup" onSubmit={handleSubmit}>
      <header className="setup__head">
        <h2>Start a screening interview</h2>
        <p className="muted">
          Upload your resume and pick a role. The system parses your resume,
          retrieves role-specific material from its knowledge base, and
          generates questions tailored to you.
        </p>
      </header>

      <div className="setup__grid">
        <div className="setup__col">
          <label className="field field--box">
            <span>Your name (optional)</span>
            <input
              type="text"
              value={candidateName}
              placeholder="e.g. Alex Doe"
              onChange={(e) => setCandidateName(e.target.value)}
            />
          </label>

          <label className="field field--box">
            <span>Target role</span>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>

          {selectedRole && (
            <div className="role-detail">
              <p className="muted">{selectedRole.description}</p>
              <span className={`badge ${kbReady ? "badge--ok" : "badge--warn"}`}>
                {kbReady
                  ? `Knowledge base: ${selectedRole.document_count} chunks`
                  : "Knowledge base empty — run ingestion for grounded questions"}
              </span>
            </div>
          )}
        </div>

        <div className="setup__col">
          <div className="field field--resume">
            <span>Resume</span>
            <div className="toggle">
              <button
                type="button"
                className={mode === "upload" ? "toggle__btn active" : "toggle__btn"}
                onClick={() => setMode("upload")}
                aria-pressed={mode === "upload"}
              >
                Upload file
              </button>
              <button
                type="button"
                className={mode === "paste" ? "toggle__btn active" : "toggle__btn"}
                onClick={() => setMode("paste")}
                aria-pressed={mode === "paste"}
              >
                Paste text
              </button>
            </div>

            {mode === "upload" ? (
              <input
                type="file"
                accept=".pdf,.txt,.md"
                aria-label="Resume file"
                onChange={(e) => setFile(e.target.files[0] || null)}
              />
            ) : (
              <textarea
                rows={8}
                value={resumeText}
                aria-label="Resume text"
                placeholder="Paste your resume text here…"
                onChange={(e) => setResumeText(e.target.value)}
              />
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      <button
        className="btn btn--primary btn--bar"
        type="submit"
        disabled={loading}
      >
        <span>{loading ? "Preparing your interview…" : "Begin interview"}</span>
        {loading && (
          <span className="btn__note">
            Parsing resume, retrieving context, and generating the first
            question — this can take a few seconds.
          </span>
        )}
      </button>
    </form>
  );
}
