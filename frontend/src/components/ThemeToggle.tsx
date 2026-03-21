import { useTheme } from "../hooks/useTheme";
import { ThemeToggleButton } from "./ui";

export function ThemeToggle() {
    const { themeMode, setThemeMode } = useTheme();

    return (
        <ThemeToggleButton
            className="theme-toggle"
            themeMode={themeMode}
            onChangeTheme={setThemeMode}
        />
    );
}
