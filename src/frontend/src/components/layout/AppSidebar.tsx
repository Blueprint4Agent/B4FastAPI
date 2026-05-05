import { AppWindow, PanelLeftClose, PanelLeftOpen, Settings } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

type SidebarKey = "show-case" | "settings";

type AppSidebarProps = {
    expanded: boolean;
    onToggleExpanded: () => void;
};

export function AppSidebar({ expanded, onToggleExpanded }: AppSidebarProps) {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();

    const items = useMemo(
        () => [
            {
                key: "show-case" as const,
                label: t("nav.sidebar.showCase"),
                icon: AppWindow,
            },
            {
                key: "settings" as const,
                label: t("nav.sidebar.settings"),
                icon: Settings,
            },
        ],
        [t],
    );

    const activeKey: SidebarKey = location.pathname.startsWith("/settings")
        ? "settings"
        : "show-case";

    const handleSelect = (key: SidebarKey) => {
        if (key === "settings") {
            navigate("/settings");
            return;
        }
        navigate("/show-case");
    };

    return (
        <aside className={expanded ? "app-sidebar app-sidebar--expanded" : "app-sidebar"}>
            <button
                type="button"
                className="app-sidebar__toggle"
                onClick={onToggleExpanded}
                aria-label={expanded ? t("nav.sidebar.toggleClose") : t("nav.sidebar.toggleOpen")}
                title={expanded ? t("nav.sidebar.toggleClose") : t("nav.sidebar.toggleOpen")}
            >
                {expanded ? <PanelLeftClose /> : <PanelLeftOpen />}
            </button>
            <nav className="app-sidebar__nav" aria-label={t("nav.sidebar.aria")}>
                {items.map(({ key, label, icon: Icon }) => {
                    const isActive = activeKey === key;
                    const buttonClassName = isActive
                        ? "app-sidebar__item app-sidebar__item--active"
                        : "app-sidebar__item";
                    return (
                        <button
                            key={key}
                            type="button"
                            className={buttonClassName}
                            onClick={() => handleSelect(key)}
                            aria-current={isActive ? "page" : undefined}
                            title={label}
                        >
                            <span className="app-sidebar__item-icon" aria-hidden="true">
                                <Icon />
                            </span>
                            {expanded ? (
                                <span className="app-sidebar__item-label">{label}</span>
                            ) : null}
                        </button>
                    );
                })}
            </nav>
        </aside>
    );
}
