import { useTranslation } from "react-i18next";

import { useTheme } from "../hooks/useTheme";
import { Button } from "./ui";

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();

  return (
    <Button className="theme-toggle" onClick={toggleTheme} type="button">
      {theme === "dark" ? t("theme.light") : t("theme.dark")}
    </Button>
  );
}
