import { useEffect, useState } from "react";

// Light/dark theme with localStorage persistence. Dark is the default; light
// only applies when the user has explicitly chosen it.
// The chosen theme is stamped on <html data-theme="…"> and CSS keys off it.
export function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem("theme") === "light" ? "light" : "dark";
    } catch {
      return "dark";
    }
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {
      // Storage unavailable (private mode etc.) — theme still applies.
    }
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  return { theme, toggle };
}
