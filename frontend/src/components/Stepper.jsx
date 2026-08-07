const LABELS = {
  setup: "1 · Setup",
  interview: "2 · Interview",
  summary: "3 · Summary",
};

export default function Stepper({ stages, current }) {
  const currentIndex = stages.indexOf(current);
  return (
    <ol className="stepper">
      {stages.map((s, i) => {
        const state =
          i < currentIndex ? "done" : i === currentIndex ? "active" : "todo";
        return (
          <li key={s} className={`stepper__item stepper__item--${state}`}>
            {LABELS[s]}
          </li>
        );
      })}
    </ol>
  );
}
