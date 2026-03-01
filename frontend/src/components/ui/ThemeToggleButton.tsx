import { Moon, Sun } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";
import { useTranslation } from "react-i18next";

type Theme = "light" | "dark";

type ThemeToggleButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onClick" | "type"> & {
  onToggle: () => void;
  theme: Theme;
};

export function ThemeToggleButton({ className, onToggle, theme, ...props }: ThemeToggleButtonProps) {
  const { t } = useTranslation();
  const isDark = theme === "dark";
  const nextClassName = className ? `theme-toggle-button ${className}` : "theme-toggle-button";

  return (
    <button
      type="button"
      className={nextClassName}
      onClick={onToggle}
      aria-label={isDark ? t("theme.dark") : t("theme.light")}
      aria-pressed={isDark}
      {...props}
    >
      <span className="theme-toggle-button__content">
        <span className="theme-toggle-button__leading-icon" aria-hidden="true">
          {isDark ? <Moon /> : <Sun />}
        </span>
        <span className="theme-toggle-button__label">{isDark ? t("theme.dark") : t("theme.light")}</span>
      </span>
      <span
        className={isDark ? "theme-toggle-button__switch theme-toggle-button__switch--on" : "theme-toggle-button__switch"}
        aria-hidden="true"
      >
        <span className="theme-toggle-button__thumb" />
      </span>
    </button>
  );
}
