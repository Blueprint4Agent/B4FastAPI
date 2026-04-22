import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { ThemeToggle } from "../../components/ui/toggles/ThemeToggle";
import { Button, InlineMessage, InputField, PanelCard } from "../../components/ui";
import { useAuthApi } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";
import { isValidEmail } from "../../utils/validation";

export function ForgotPasswordPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { requestPasswordReset, extractApiDetail, resolveAuthErrorMessage } = useAuthApi();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const [email, setEmail] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [warningMessage, setWarningMessage] = useState("");
    const emailEnabled = appConfig?.email_enabled === true;

    const onSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setSubmitting(true);
        setErrorMessage("");
        setWarningMessage("");

        if (configLoading) {
            setWarningMessage(t("forgotPassword.configLoading"));
            setSubmitting(false);
            return;
        }
        if (!emailEnabled) {
            setWarningMessage(t("forgotPassword.disabled"));
            setSubmitting(false);
            return;
        }
        if (!email.trim()) {
            setWarningMessage(t("auth.errors.requiredEmail"));
            setSubmitting(false);
            return;
        }
        if (!isValidEmail(email)) {
            setWarningMessage(t("auth.errors.invalidEmail"));
            setSubmitting(false);
            return;
        }

        try {
            await requestPasswordReset(email.trim());
            navigate("/forgot-password/email-sent", {
                replace: true,
                state: { email: email.trim() },
            });
        } catch (nextError) {
            const detail = extractApiDetail(nextError);
            if (detail?.error === "EMAIL_DISABLED") {
                setWarningMessage(t("forgotPassword.disabled"));
            } else {
                setErrorMessage(
                    resolveAuthErrorMessage(t, detail, "forgotPassword.requestFallback"),
                );
            }
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <main className="page">
            <ThemeToggle />
            <PanelCard title={t("forgotPassword.title")} subtitle={t("forgotPassword.subtitle")}>
                <form onSubmit={onSubmit} className="form" noValidate>
                    <InputField
                        label={t("forgotPassword.emailLabel")}
                        type="email"
                        autoComplete="email"
                        value={email}
                        onValueChange={(value) => {
                            setEmail(value);
                            if (warningMessage || errorMessage) {
                                setWarningMessage("");
                                setErrorMessage("");
                            }
                        }}
                    />
                    {warningMessage ? <InlineMessage>{warningMessage}</InlineMessage> : null}
                    {errorMessage ? <InlineMessage>{errorMessage}</InlineMessage> : null}
                    <Button
                        type="submit"
                        loading={submitting}
                        disabled={configLoading || !emailEnabled}
                    >
                        {t("forgotPassword.submitIdle")}
                    </Button>
                </form>
                <p className="muted auth-footer">
                    {t("forgotPassword.loginPrompt")}{" "}
                    <Link to="/login" className="text-link">
                        {t("forgotPassword.loginLink")}
                    </Link>
                </p>
            </PanelCard>
        </main>
    );
}
