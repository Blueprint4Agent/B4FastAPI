import { useTheme } from "../hooks/useTheme";
import { ThemeToggleButton } from "./ui";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <ThemeToggleButton className="theme-toggle" onToggle={toggleTheme} theme={theme} />
  );
}
