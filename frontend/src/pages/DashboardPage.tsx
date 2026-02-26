import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { ThemeToggle } from "../components/ThemeToggle";
import { Button, KeyValueCard, PanelCard } from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";

export function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout } = useAuthContext();
  const [busy, setBusy] = useState(false);

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
    <main className="page">
      <ThemeToggle />
      <PanelCard title={t("dashboard.title")} subtitle={t("dashboard.subtitle")}>
        <dl className="meta">
          <KeyValueCard label={t("dashboard.labels.userId")} value={user?.id ?? "-"} />
          <KeyValueCard label={t("dashboard.labels.name")} value={user?.name ?? "-"} />
          <KeyValueCard label={t("dashboard.labels.email")} value={user?.email ?? "-"} />
        </dl>
        <Button onClick={onLogout} disabled={busy}>
          {busy ? t("dashboard.logoutBusy") : t("dashboard.logoutIdle")}
        </Button>
      </PanelCard>
    </main>
  );
}
