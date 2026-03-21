import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuthContext } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { BrandMark, ProfileDropdown } from "./ui";

export function AppNavbar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthContext();
  const { themeMode, setThemeMode } = useTheme();
  const [busy, setBusy] = useState(false);

  const displayName = user?.name?.trim() || user?.email || "User";
  const avatarLabel = displayName.slice(0, 1).toUpperCase();
  let pageTitle = t("nav.pageTitles.showCase");
  if (location.pathname === "/settings") {
    pageTitle = t("nav.pageTitles.settings");
  } else if (location.pathname === "/show-case/loading") {
    pageTitle = t("nav.pageTitles.loading");
  } else if (location.pathname === "/show-case/404" || !location.pathname.startsWith("/show-case")) {
    pageTitle = t("nav.pageTitles.notFound");
  }

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
        <Link to="/show-case" className="app-nav__brand" aria-label={t("nav.aria.goDashboard")}>
          <BrandMark className="brand-mark--nav" />
        </Link>
        <p className="app-nav__title">{pageTitle}</p>
        <ProfileDropdown
          avatarLabel={avatarLabel}
          busy={busy}
          displayName={displayName}
          email={user?.email}
          onLogout={() => void onLogout()}
          onChangeTheme={setThemeMode}
          themeMode={themeMode}
        />
      </div>
    </header>
  );
}
