import { RefreshCw, WifiOff } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useServerConnectivity } from "../../hooks/connectivity/useServerConnectivity";

export function ConnectivityBanner() {
    const { t } = useTranslation();
    const { isDesktop, status, checkNow } = useServerConnectivity();

    if (!isDesktop || status === "online") {
        return null;
    }

    const reconnecting = status === "checking" || status === "reconnecting";

    return (
        <div className="connectivity-banner" role="status" aria-live="polite">
            {reconnecting ? (
                <RefreshCw className="connectivity-banner__icon connectivity-banner__icon--spin" />
            ) : (
                <WifiOff className="connectivity-banner__icon" />
            )}
            <span>{reconnecting ? t("connectivity.reconnecting") : t("connectivity.offline")}</span>
            {status === "offline" ? (
                <button
                    type="button"
                    className="connectivity-banner__retry"
                    onClick={() => void checkNow()}
                >
                    {t("connectivity.retry")}
                </button>
            ) : null}
        </div>
    );
}
