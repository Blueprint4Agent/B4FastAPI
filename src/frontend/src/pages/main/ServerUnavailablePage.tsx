import { useTranslation } from "react-i18next";

import { Button, PanelCard, WarningCard } from "../../components/ui";

type ServerUnavailablePageProps = {
    checking: boolean;
    error: unknown | null;
    onRetry: () => void;
};

export function ServerUnavailablePage({ checking, error, onRetry }: ServerUnavailablePageProps) {
    const { t } = useTranslation();

    return (
        <main className="page">
            <PanelCard
                title={t("serverUnavailable.title")}
                subtitle={t("serverUnavailable.subtitle")}
                className="loading-panel"
            >
                <WarningCard
                    title={t("serverUnavailable.statusTitle")}
                    message={
                        error ? t("serverUnavailable.configError") : t("serverUnavailable.waiting")
                    }
                >
                    <div className="status-card__actions">
                        <Button loading={checking} onClick={onRetry}>
                            {checking
                                ? t("serverUnavailable.retrying")
                                : t("serverUnavailable.retry")}
                        </Button>
                    </div>
                </WarningCard>
            </PanelCard>
        </main>
    );
}
