import { useEffect, useState } from "react";

type Theme = "light" | "dark";
const THEME_STORAGE_KEY = "blueprint4fastapi_theme";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  return {
    theme,
    toggleTheme: () => setTheme((prev) => (prev === "dark" ? "light" : "dark"))
  };
}
