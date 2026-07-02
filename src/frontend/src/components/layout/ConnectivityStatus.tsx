import { RefreshCw, WifiOff } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useServerConnectivity } from "../../hooks/connectivity/useServerConnectivity";

type ConnectivityStatusProps = {
    placement: "navbar" | "titlebar";
};

export function ConnectivityStatus({ placement }: ConnectivityStatusProps) {
    const { t } = useTranslation();
    const { isDesktop, status, checkNow } = useServerConnectivity();
    const [manualRetrying, setManualRetrying] = useState(false);

    if (!isDesktop || status === "online") {
        return null;
    }

    const reconnecting = status === "checking" || status === "reconnecting";
    const showReconnecting = reconnecting && !manualRetrying;
    const className = `connectivity-status connectivity-status--${placement}`;
    const content = (
        <>
            {showReconnecting ? (
                <RefreshCw className="connectivity-status__icon connectivity-status__icon--spin" />
            ) : (
                <WifiOff className="connectivity-status__icon" />
            )}
            <span>
                {showReconnecting
                    ? t("connectivity.reconnectingShort")
                    : t("connectivity.offlineShort")}
            </span>
        </>
    );

    return (
        <div className={className} role="status" aria-live="polite">
            {showReconnecting ? (
                <span
                    className="connectivity-status__content"
                    title={t("connectivity.reconnecting")}
                >
                    {content}
                </span>
            ) : (
                <button
                    type="button"
                    className={`connectivity-status__content connectivity-status__retry${
                        manualRetrying ? " connectivity-status__content--pending" : ""
                    }`}
                    aria-label={t("connectivity.retry")}
                    aria-busy={manualRetrying}
                    disabled={manualRetrying}
                    title={t("connectivity.offline")}
                    onClick={() => {
                        setManualRetrying(true);
                        void checkNow().finally(() => setManualRetrying(false));
                    }}
                >
                    {content}
                </button>
            )}
        </div>
    );
}
