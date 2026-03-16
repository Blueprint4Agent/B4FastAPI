import { LogOut, Settings } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import type { ThemeMode } from "../../hooks/useTheme";
import { ThemeToggleButton } from "./ThemeToggleButton";

type ProfileDropdownProps = {
  avatarLabel: string;
  busy: boolean;
  displayName: string;
  email?: string;
  onLogout: () => void;
  onChangeTheme: (mode: ThemeMode) => void;
  themeMode: ThemeMode;
};

export function ProfileDropdown({
  avatarLabel,
  busy,
  displayName,
  email,
  onLogout,
  onChangeTheme,
  themeMode
}: ProfileDropdownProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  return (
    <div className="profile-menu" ref={menuRef}>
      <button
        type="button"
        className="profile-menu__trigger"
        aria-label={t("nav.aria.openMenu")}
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((prev) => !prev)}
        title={displayName}
      >
        <span className="profile-menu__avatar" aria-hidden="true">
          {avatarLabel}
        </span>
      </button>
      {menuOpen ? (
        <div className="profile-menu__dropdown" role="menu" aria-label={t("nav.profileMenu")}>
          <p className="profile-menu__email">{email}</p>
          <Link to="/settings" className="profile-menu__item" role="menuitem">
            <span className="profile-menu__item-icon" aria-hidden="true">
              <Settings />
            </span>
            <span>{t("nav.settings")}</span>
          </Link>
          <button
            type="button"
            className="profile-menu__item profile-menu__item--danger"
            role="menuitem"
            onClick={onLogout}
            disabled={busy}
          >
            <span className="profile-menu__item-icon" aria-hidden="true">
              <LogOut />
            </span>
            <span>{busy ? t("nav.logoutBusy") : t("nav.logoutIdle")}</span>
          </button>
          <ThemeToggleButton
            className="profile-menu__item"
            role="menuitem"
            themeMode={themeMode}
            onChangeTheme={onChangeTheme}
          />
        </div>
      ) : null}
    </div>
  );
}
