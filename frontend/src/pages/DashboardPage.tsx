import { useTranslation } from "react-i18next";

import { KeyValueCard, PanelCard } from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthContext();

  return (
    <section className="page-content">
      <PanelCard title={t("dashboard.title")} subtitle={t("dashboard.subtitle")}>
        <dl className="meta">
          <KeyValueCard label={t("dashboard.labels.userId")} value={user?.id ?? "-"} />
          <KeyValueCard label={t("dashboard.labels.name")} value={user?.name ?? "-"} />
          <KeyValueCard label={t("dashboard.labels.email")} value={user?.email ?? "-"} />
        </dl>
      </PanelCard>
    </section>
  );
}
