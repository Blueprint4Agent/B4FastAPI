import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { useAuthContext } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { BrandMark, ProfileDropdown } from "./ui";

export function AppNavbar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();
  const { theme, toggleTheme } = useTheme();
  const [busy, setBusy] = useState(false);

  const displayName = user?.name?.trim() || user?.email || "User";
  const avatarLabel = displayName.slice(0, 1).toUpperCase();

  const onLogout = async () => {
    setBusy(true);
    try {
      await logout();
      navigate("/login", { replace: true });
    } finally {
      setBusy(false);
    }
  };

  return (
    <header className="app-nav">
      <div className="app-nav__inner">
        <Link to="/dashboard" className="app-nav__brand" aria-label={t("nav.aria.goDashboard")}>
          <BrandMark className="brand-mark--nav" />
        </Link>
        <ProfileDropdown
          avatarLabel={avatarLabel}
          busy={busy}
          displayName={displayName}
          email={user?.email}
          onLogout={() => void onLogout()}
          onToggleTheme={toggleTheme}
          theme={theme}
        />
      </div>
    </header>
  );
}
