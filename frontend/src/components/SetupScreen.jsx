import { useEffect, useState } from "react";
import { getRoles, startInterview } from "../api.js";

// Candidate entry: type (or pick) a role, provide a resume (upload or paste),
// start. Any role is accepted; the presets are shortcuts that come with their
// own knowledge base.
const MAX_ROLE_CHARS = 60;
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
      })
      .catch((e) => setError(`Could not load suggested roles: ${e.message}`));
  }, []);

  const roleKey = role.trim().toLowerCase();
  const selectedRole = roles.find(
    (r) => r.label.toLowerCase() === roleKey || r.id === roleKey
  );
  const kbReady = selectedRole && selectedRole.document_count > 0;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!role.trim()) return setError("Please enter a target role.");
    if (mode === "upload" && !file) return setError("Please upload a resume file.");
    if (mode === "paste" && !resumeText.trim())
      return setError("Please paste your resume text.");

    setLoading(true);
    try {
      const res = await startInterview({
        role: role.trim(),
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
          Upload your resume and enter the role you're applying for. The
          system parses your resume, retrieves relevant material from its
          knowledge base, and generates questions tailored to you.
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
            <input
              type="text"
              value={role}
              maxLength={MAX_ROLE_CHARS}
              placeholder="e.g. Frontend Developer"
              onChange={(e) => setRole(e.target.value)}
            />
          </label>

          {roles.length > 0 && (
            <div className="role-presets">
              <span className="role-presets__label" id="role-presets-label">
                Or pick one
              </span>
              <div
                className="role-presets__list"
                role="group"
                aria-labelledby="role-presets-label"
              >
                {roles.map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    className={
                      selectedRole?.id === r.id
                        ? "role-preset active"
                        : "role-preset"
                    }
                    aria-pressed={selectedRole?.id === r.id}
                    onClick={() => setRole(r.label)}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedRole ? (
            <div className="role-detail">
              <p className="muted">{selectedRole.description}</p>
              <span className={`badge ${kbReady ? "badge--ok" : "badge--warn"}`}>
                {kbReady
                  ? `Knowledge base: ${selectedRole.document_count} chunks`
                  : "Knowledge base empty — run ingestion for grounded questions"}
              </span>
            </div>
          ) : (
            role.trim() && (
              <div className="role-detail">
                <p className="muted">
                  Custom role. Questions are grounded in the knowledge base
                  where it's relevant to this role; otherwise they're generated
                  from the role's core concepts.
                </p>
                <span className="badge">Custom role</span>
              </div>
            )
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
