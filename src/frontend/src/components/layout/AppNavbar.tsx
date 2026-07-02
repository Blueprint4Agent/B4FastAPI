import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuthContext } from "../../hooks/useAuth";
import { useAppConfig } from "../../hooks/useFeatures";
import { useTheme } from "../../hooks/useTheme";
import { startDesktopWindowDrag } from "../../utils/desktopWindow";
import { BrandMark, Tooltip } from "../ui";
import { ProfileDropdown } from "./ProfileDropdown";

export function AppNavbar() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuthContext();
    const { data: appConfig } = useAppConfig();
    const { themeMode, setThemeMode } = useTheme();
    const [busy, setBusy] = useState(false);
    const loginEnabled = appConfig?.login_enabled === true;

    const displayName = user?.name?.trim() || user?.email;
    const avatarLabel = displayName?.slice(0, 1).toUpperCase();
    let pageTitle = t("nav.pageTitles.showCase");
    if (location.pathname === "/settings") {
        pageTitle = t("nav.pageTitles.settings");
    } else if (location.pathname === "/show-case/loading") {
        pageTitle = t("nav.pageTitles.loading");
    } else if (
        location.pathname === "/show-case/404" ||
        !location.pathname.startsWith("/show-case")
    ) {
        pageTitle = t("nav.pageTitles.notFound");
    }

    const onLogout = async () => {
        setBusy(true);
        try {
            await logout();
            navigate(loginEnabled ? "/login" : "/show-case", { replace: true });
        } finally {
            setBusy(false);
        }
    };

    return (
        <header className="app-nav" data-tauri-drag-region onMouseDown={startDesktopWindowDrag}>
            <div className="app-nav__inner" data-tauri-drag-region>
                <Tooltip content={t("nav.aria.goShowCase")} side="right">
                    <Link
                        to="/show-case"
                        className="app-nav__brand"
                        aria-label={t("nav.aria.goShowCase")}
                    >
                        <BrandMark className="brand-mark--nav" />
                    </Link>
                </Tooltip>
                <p className="app-nav__title">{pageTitle}</p>
                {user && displayName && avatarLabel ? (
                    <ProfileDropdown
                        avatarLabel={avatarLabel}
                        avatarImageUrl={user.profile_image_url}
                        busy={busy}
                        displayName={displayName}
                        email={user.email}
                        onLogout={() => void onLogout()}
                        onChangeTheme={setThemeMode}
                        showLogout={loginEnabled}
                        themeMode={themeMode}
                    />
                ) : null}
            </div>
        </header>
    );
}
