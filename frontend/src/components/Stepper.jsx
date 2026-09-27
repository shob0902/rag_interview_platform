const LABELS = {
  setup: "Setup",
  interview: "Interview",
  summary: "Summary",
};

export default function Stepper({ stages, current }) {
  const currentIndex = stages.indexOf(current);
  return (
    <ol className="stepper" aria-label="Interview progress">
      {stages.map((s, i) => {
        const state =
          i < currentIndex ? "done" : i === currentIndex ? "active" : "todo";
        return (
          <li
            key={s}
            className={`stepper__item stepper__item--${state}`}
            aria-current={state === "active" ? "step" : undefined}
          >
            <span className="stepper__num">{String(i + 1).padStart(2, "0")}</span>
            <span className="stepper__label">{LABELS[s]}</span>
          </li>
        );
      })}
    </ol>
  );
}
