// Sidebar showing the structured resume profile the backend extracted. This
// makes it visible that the interview is genuinely resume-driven.
function Chips({ title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="profile__group">
      <h4>{title}</h4>
      <div className="chips">
        {items.map((it) => (
          <span key={it} className="chip">
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function ProfilePanel({ profile, name }) {
  if (!profile) return null;
  return (
    <div className="card profile">
      <h3>{name || "Candidate"}</h3>
      {profile.seniority && profile.seniority !== "unknown" && (
        <span className="badge badge--muted">{profile.seniority} level</span>
      )}
      {profile.experience_summary && (
        <p className="muted small">{profile.experience_summary}</p>
      )}
      <Chips title="Skills" items={profile.skills} />
      <Chips title="Technologies" items={profile.technologies} />
      <Chips title="Domains" items={profile.domains} />
    </div>
  );
}
