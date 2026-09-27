// Sidebar showing the structured resume profile the backend extracted. This
// makes it visible that the interview is genuinely resume-driven.
// variant="compact" shows only the name, seniority, skills and technologies.
function Chips({ title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="profile__group">
      <h4>{title}</h4>
      <p className="chips">{items.join(" / ")}</p>
    </div>
  );
}

export default function ProfilePanel({ profile, name, variant = "full" }) {
  if (!profile) return null;
  const compact = variant === "compact";
  return (
    <div className={compact ? "profile profile--compact" : "profile"}>
      <h3>{name || "Candidate"}</h3>
      {profile.seniority && profile.seniority !== "unknown" && (
        <span className="badge badge--muted">{profile.seniority} level</span>
      )}
      {!compact && profile.experience_summary && (
        <p className="muted small profile__summary">
          {profile.experience_summary}
        </p>
      )}
      <Chips title="Skills" items={profile.skills} />
      <Chips title="Technologies" items={profile.technologies} />
      {!compact && <Chips title="Domains" items={profile.domains} />}
    </div>
  );
}
