import { useTranslation } from "react-i18next";

import { KeyValueCard, PanelCard } from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";

export function SettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuthContext();

  return (
    <section className="page-content">
      <PanelCard title={t("settings.title")} subtitle={t("settings.subtitle")}>
        <dl className="meta">
          <KeyValueCard label={t("settings.labels.name")} value={user?.name ?? "-"} />
          <KeyValueCard label={t("settings.labels.email")} value={user?.email ?? "-"} />
          <KeyValueCard label={t("settings.labels.userId")} value={user?.id ?? "-"} />
        </dl>
        <p className="muted">{t("settings.hint")}</p>
      </PanelCard>
    </section>
  );
}
