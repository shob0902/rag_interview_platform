// Thin API client. All calls go through the Vite proxy to the FastAPI backend.

const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function getRoles() {
  return handle(await fetch(`${BASE}/roles`));
}

export async function getHealth() {
  return handle(await fetch(`${BASE}/health`));
}

// Starts an interview. Either `file` (File object) or `resumeText` must be set.
export async function startInterview({ role, candidateName, file, resumeText }) {
  const form = new FormData();
  form.append("role", role);
  form.append("candidate_name", candidateName || "Candidate");
  if (file) form.append("resume_file", file);
  if (resumeText) form.append("resume_text", resumeText);

  return handle(
    await fetch(`${BASE}/interviews/start`, { method: "POST", body: form })
  );
}

export async function submitAnswer(sessionId, answer) {
  return handle(
    await fetch(`${BASE}/interviews/${sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    })
  );
}

export async function getSession(sessionId) {
  return handle(await fetch(`${BASE}/interviews/${sessionId}`));
}
