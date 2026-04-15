import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { InfoCard } from "../components/StatusCard";
import { ThemeToggle } from "../components/ThemeToggle";
import { Button, PanelCard } from "../components/ui";

export function ResetPasswordSuccessPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();

    return (
        <main className="page">
            <ThemeToggle />
            <PanelCard
                title={t("resetPassword.successTitle")}
                subtitle={t("resetPassword.successSubtitle")}
            >
                <InfoCard
                    title={t("cards.infoTitle")}
                    message={t("resetPassword.successDescription")}
                />
                <div className="verify-email__actions">
                    <Button type="button" onClick={() => navigate("/login", { replace: true })}>
                        {t("resetPassword.backToLogin")}
                    </Button>
                </div>
            </PanelCard>
        </main>
    );
}
