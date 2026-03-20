import { useTranslation } from "react-i18next";

import { PanelCard, Spinner } from "../components/ui";

type LoadingPageProps = {
  message?: string;
};

export function LoadingPage({ message }: LoadingPageProps) {
  const { t } = useTranslation();
  const loadingMessage = message ?? t("app.loadingSession");

  return (
    <main className="page">
      <PanelCard title={t("app.loadingTitle")} subtitle={t("app.loadingSubtitle")} className="loading-panel">
        <div className="loading-panel__body">
          <Spinner size="lg" label={loadingMessage} />
        </div>
      </PanelCard>
    </main>
  );
}
