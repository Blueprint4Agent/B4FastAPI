import { Laptop, Moon, Sun } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";
import { useTranslation } from "react-i18next";

import type { ThemeMode } from "../../hooks/useTheme";

type ThemeToggleButtonProps = Omit<ButtonHTMLAttributes<HTMLDivElement>, "onChange"> & {
    onChangeTheme: (mode: ThemeMode) => void;
    themeMode: ThemeMode;
};

export function ThemeToggleButton({
    className,
    onChangeTheme,
    themeMode,
    ...props
}: ThemeToggleButtonProps) {
    const { t } = useTranslation();
    const nextClassName = className ? `theme-toggle-button ${className}` : "theme-toggle-button";

    return (
        <div className={nextClassName} role="group" aria-label={t("theme.select")} {...props}>
            <span className="theme-toggle-button__title">{t("theme.label")}</span>
            <button
                type="button"
                className={
                    themeMode === "system"
                        ? "theme-toggle-button__option theme-toggle-button__option--active"
                        : "theme-toggle-button__option"
                }
                onClick={() => onChangeTheme("system")}
                aria-pressed={themeMode === "system"}
                aria-label={t("theme.system")}
                title={t("theme.system")}
            >
                <Laptop />
            </button>
            <button
                type="button"
                className={
                    themeMode === "light"
                        ? "theme-toggle-button__option theme-toggle-button__option--active"
                        : "theme-toggle-button__option"
                }
                onClick={() => onChangeTheme("light")}
                aria-pressed={themeMode === "light"}
                aria-label={t("theme.light")}
                title={t("theme.light")}
            >
                <Sun />
            </button>
            <button
                type="button"
                className={
                    themeMode === "dark"
                        ? "theme-toggle-button__option theme-toggle-button__option--active"
                        : "theme-toggle-button__option"
                }
                onClick={() => onChangeTheme("dark")}
                aria-pressed={themeMode === "dark"}
                aria-label={t("theme.dark")}
                title={t("theme.dark")}
            >
                <Moon />
            </button>
        </div>
    );
}
