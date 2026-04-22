import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { ThemeToggle } from "../../components/ui/toggles/ThemeToggle";
import { OAuthOptionsCard } from "../../components/features/auth/OAuthOptionsCard";
import { OAuthProviderButton } from "../../components/features/auth/OAuthProviderButton";
import {
    BrandMark,
    Button,
    FormCheckbox,
    InputField,
    InlineMessage,
    PanelCard,
} from "../../components/ui";
import { useAuthContext } from "../../hooks/useAuth";
import { useAuthApi, type OAuthProvider } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";
import { isValidEmail, isValidPassword } from "../../utils/validation";

const REMEMBER_EMAIL_STORAGE_KEY = "template_remember_email";
const REMEMBER_EMAIL_ENABLED_STORAGE_KEY = "template_remember_email_enabled";
const REMEMBER_ME_ENABLED_STORAGE_KEY = "template_remember_me_enabled";

export function LoginPage() {
    const { t } = useTranslation();
    const { login } = useAuthContext();
    const {
        getOAuthProviders,
        resendVerificationEmail,
        extractApiDetail,
        resolveAuthErrorMessage,
    } = useAuthApi();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const [rememberEmail, setRememberEmail] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [resending, setResending] = useState(false);
    const [showResendButton, setShowResendButton] = useState(false);
    const [resendMessage, setResendMessage] = useState("");
    const [emailErrorMessage, setEmailErrorMessage] = useState("");
    const [passwordErrorMessage, setPasswordErrorMessage] = useState("");
    const [oauthProviders, setOAuthProviders] = useState<
        Array<{ provider: OAuthProvider; start_path: string }>
    >([]);
    const loginEnabled = appConfig?.login_enabled !== false;
    const emailEnabled = appConfig?.email_enabled === true;
    const oauthEnabled = appConfig?.oauth_enabled === true;

    useEffect(() => {
        try {
            const rememberMeEnabled =
                window.localStorage.getItem(REMEMBER_ME_ENABLED_STORAGE_KEY) === "true";
            setRememberMe(rememberMeEnabled);

            const rememberEmailEnabled =
                window.localStorage.getItem(REMEMBER_EMAIL_ENABLED_STORAGE_KEY) === "true";
            if (!rememberEmailEnabled) {
                setRememberEmail(false);
                return;
            }
            const rememberedEmail = window.localStorage.getItem(REMEMBER_EMAIL_STORAGE_KEY);
            if (rememberedEmail) {
                setEmail(rememberedEmail);
                setRememberEmail(true);
            }
        } catch {
            // ignore storage errors in restricted browser contexts
        }
    }, []);

    useEffect(() => {
        const run = async () => {
            if (!oauthEnabled || !loginEnabled) {
                setOAuthProviders([]);
                return;
            }
            try {
                const payload = await getOAuthProviders();
                setOAuthProviders(payload.providers);
            } catch {
                setOAuthProviders([]);
            }
        };
        void run();
    }, [oauthEnabled, loginEnabled]);

    const onSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setSubmitting(true);
        setEmailErrorMessage("");
        setPasswordErrorMessage("");
        setShowResendButton(false);
        setResendMessage("");

        if (!loginEnabled) {
            setPasswordErrorMessage(t("auth.errors.loginDisabled"));
            setSubmitting(false);
            return;
        }

        if (!email.trim()) {
            setEmailErrorMessage(t("auth.errors.requiredEmail"));
            setSubmitting(false);
            return;
        }
        if (!isValidEmail(email)) {
            setEmailErrorMessage(t("auth.errors.invalidEmail"));
            setSubmitting(false);
            return;
        }
        if (!password.trim()) {
            setPasswordErrorMessage(t("auth.errors.requiredPassword"));
            setSubmitting(false);
            return;
        }
        if (!isValidPassword(password)) {
            setPasswordErrorMessage(t("auth.errors.invalidPasswordPattern"));
            setSubmitting(false);
            return;
        }

        try {
            await login({ email, password, remember_me: rememberMe });
            try {
                window.localStorage.setItem(
                    REMEMBER_ME_ENABLED_STORAGE_KEY,
                    rememberMe ? "true" : "false",
                );
                if (rememberEmail) {
                    window.localStorage.setItem(REMEMBER_EMAIL_ENABLED_STORAGE_KEY, "true");
                    window.localStorage.setItem(REMEMBER_EMAIL_STORAGE_KEY, email.trim());
                } else {
                    window.localStorage.setItem(REMEMBER_EMAIL_ENABLED_STORAGE_KEY, "false");
                    window.localStorage.removeItem(REMEMBER_EMAIL_STORAGE_KEY);
                }
            } catch {
                // ignore storage errors in restricted browser contexts
            }
            navigate("/show-case", { replace: true });
        } catch (nextError) {
            const detail = extractApiDetail(nextError);
            const code = detail?.error;
            const details = detail?.details;

            if (code === "INVALID_CREDENTIALS" && typeof details?.remaining_attempts === "number") {
                setPasswordErrorMessage(
                    t("auth.errors.invalidCredentialsWithCount", {
                        count: details.remaining_attempts,
                    }),
                );
            } else if (
                code === "ACCOUNT_LOCKED" &&
                typeof details?.remaining_seconds === "number"
            ) {
                setPasswordErrorMessage(
                    t("auth.errors.accountLocked", { seconds: details.remaining_seconds }),
                );
            } else if (code === "EMAIL_NOT_VERIFIED") {
                setEmailErrorMessage(t("auth.errors.emailNotVerified"));
                setShowResendButton(true);
            } else {
                setPasswordErrorMessage(
                    resolveAuthErrorMessage(t, detail, "auth.errors.loginFallback"),
                );
            }
        } finally {
            setSubmitting(false);
        }
    };

    const onResendVerification = async () => {
        if (!email.trim() || resending) return;
        setResending(true);
        setResendMessage("");
        try {
            const payload = await resendVerificationEmail(email.trim());
            setResendMessage(payload.message);
        } catch {
            setResendMessage(t("auth.errors.resendVerificationFallback"));
        } finally {
            setResending(false);
        }
    };

    return (
        <main className="page">
            <ThemeToggle />
            <div className="auth-panel-stack">
                <BrandMark className="brand-mark--login" />
                <PanelCard title={t("login.title")} subtitle={t("login.subtitle")}>
                    {loginEnabled ? (
                        <form onSubmit={onSubmit} className="form" noValidate>
                            <InputField
                                label={t("login.fields.email")}
                                type="email"
                                autoComplete="email"
                                value={email}
                                onValueChange={(value) => {
                                    setEmail(value);
                                    if (emailErrorMessage || resendMessage || showResendButton) {
                                        setEmailErrorMessage("");
                                        setResendMessage("");
                                        setShowResendButton(false);
                                    }
                                }}
                            />
                            {emailErrorMessage ? (
                                <InlineMessage>{emailErrorMessage}</InlineMessage>
                            ) : null}
                            {showResendButton ? (
                                <div className="login-inline-actions">
                                    <Button
                                        type="button"
                                        loading={resending}
                                        onClick={onResendVerification}
                                    >
                                        {t("auth.actions.resendVerification")}
                                    </Button>
                                </div>
                            ) : null}
                            {resendMessage ? (
                                <InlineMessage tone="info">{resendMessage}</InlineMessage>
                            ) : null}
                            <InputField
                                label={t("login.fields.password")}
                                type="password"
                                autoComplete="current-password"
                                value={password}
                                onValueChange={(value) => {
                                    setPassword(value);
                                    if (passwordErrorMessage) {
                                        setPasswordErrorMessage("");
                                    }
                                }}
                            />
                            {passwordErrorMessage ? (
                                <InlineMessage>{passwordErrorMessage}</InlineMessage>
                            ) : null}
                            <div className="login-remember-options">
                                <FormCheckbox
                                    checked={rememberEmail}
                                    onCheckedChange={setRememberEmail}
                                    label={t("login.rememberEmail")}
                                />
                                <FormCheckbox
                                    checked={rememberMe}
                                    onCheckedChange={setRememberMe}
                                    label={t("login.rememberMe")}
                                />
                            </div>
                            <Button type="submit" loading={submitting}>
                                {t("login.submitIdle")}
                            </Button>
                        </form>
                    ) : (
                        <div className="form">
                            <InlineMessage>{t("auth.errors.loginDisabled")}</InlineMessage>
                        </div>
                    )}
                    <p className="muted auth-footer">
                        {t("login.signupPrompt")}{" "}
                        <Link to="/signup" className="text-link">
                            {t("login.signupLink")}
                        </Link>
                    </p>
                    {!configLoading && emailEnabled ? (
                        <p className="muted">
                            {t("login.forgotPasswordPrompt")}{" "}
                            <Link to="/forgot-password" className="text-link">
                                {t("login.forgotPasswordLink")}
                            </Link>
                        </p>
                    ) : null}
                    {loginEnabled && oauthProviders.length > 0 ? (
                        <OAuthOptionsCard title={t("login.oauth.divider")}>
                            <div className="oauth-provider-list">
                                {oauthProviders.map((item) => (
                                    <OAuthProviderButton
                                        key={item.provider}
                                        provider={item.provider}
                                        label={t(`login.oauth.providers.${item.provider}`)}
                                        startPath={item.start_path}
                                    />
                                ))}
                            </div>
                        </OAuthOptionsCard>
                    ) : null}
                </PanelCard>
            </div>
        </main>
    );
}
