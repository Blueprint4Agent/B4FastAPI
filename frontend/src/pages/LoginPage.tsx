import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { getOAuthProviders, resendVerificationEmail, type OAuthProvider } from "../api/authApi";
import { ErrorCard, WarningCard } from "../components/StatusCard";
import { ThemeToggle } from "../components/ThemeToggle";
import {
  BrandMark,
  Button,
  FormCheckbox,
  InputField,
  OAuthOptionsCard,
  OAuthProviderButton,
  PanelCard
} from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";
import { useAppConfig } from "../hooks/useFeatures";
import { isValidEmail, isValidPassword } from "../utils/validation";

type APIError = {
  detail?: {
    error?: string;
    message?: string;
    details?: {
      remaining_attempts?: number;
      remaining_seconds?: number;
    };
  };
};

const REMEMBER_EMAIL_STORAGE_KEY = "template_remember_email";
const REMEMBER_EMAIL_ENABLED_STORAGE_KEY = "template_remember_email_enabled";
const REMEMBER_ME_ENABLED_STORAGE_KEY = "template_remember_me_enabled";

function extractApiDetail(error: unknown): APIError["detail"] | null {
  if (!error || typeof error !== "object") return null;
  const detail = (error as APIError).detail;
  if (!detail || typeof detail !== "object") return null;
  return detail;
}

export function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuthContext();
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
  const [errorMessage, setErrorMessage] = useState("");
  const [warningMessage, setWarningMessage] = useState("");
  const [oauthProviders, setOAuthProviders] = useState<Array<{ provider: OAuthProvider; start_path: string }>>([]);
  const emailEnabled = appConfig?.email_enabled === true;
  const oauthEnabled = appConfig?.oauth_enabled === true;

  useEffect(() => {
    try {
      const rememberMeEnabled = window.localStorage.getItem(REMEMBER_ME_ENABLED_STORAGE_KEY) === "true";
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
      if (!oauthEnabled) {
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
  }, [oauthEnabled]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage("");
    setWarningMessage("");
    setShowResendButton(false);
    setResendMessage("");

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
    if (!password.trim()) {
      setWarningMessage(t("auth.errors.requiredPassword"));
      setSubmitting(false);
      return;
    }
    if (!isValidPassword(password)) {
      setWarningMessage(t("auth.errors.invalidPasswordPattern"));
      setSubmitting(false);
      return;
    }

    try {
      await login({ email, password, remember_me: rememberMe });
      try {
        window.localStorage.setItem(
          REMEMBER_ME_ENABLED_STORAGE_KEY,
          rememberMe ? "true" : "false"
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
      navigate("/dashboard", { replace: true });
    } catch (nextError) {
      const detail = extractApiDetail(nextError);
      const code = detail?.error;
      const details = detail?.details;

      if (code === "INVALID_CREDENTIALS" && typeof details?.remaining_attempts === "number") {
        setWarningMessage(
          t("auth.errors.invalidCredentialsWithCount", { count: details.remaining_attempts })
        );
      } else if (code === "ACCOUNT_LOCKED" && typeof details?.remaining_seconds === "number") {
        setWarningMessage(t("auth.errors.accountLocked", { seconds: details.remaining_seconds }));
      } else if (code === "EMAIL_NOT_VERIFIED") {
        setWarningMessage(t("auth.errors.emailNotVerified"));
        setShowResendButton(true);
      } else {
        setErrorMessage(detail?.message || detail?.error || t("auth.errors.loginFallback"));
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
          <form onSubmit={onSubmit} className="form" noValidate>
            <InputField
              label={t("login.fields.email")}
              type="email"
              autoComplete="email"
              value={email}
              onValueChange={setEmail}
            />
            <InputField
              label={t("login.fields.password")}
              type="password"
              autoComplete="current-password"
              value={password}
              onValueChange={setPassword}
            />
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
            {warningMessage ? (
              <WarningCard title={t("cards.warningTitle")} message={warningMessage}>
                <div className="status-card__actions">
                  {showResendButton ? (
                    <Button type="button" loading={resending} onClick={onResendVerification}>
                      {t("auth.actions.resendVerification")}
                    </Button>
                  ) : null}
                  {resendMessage ? <p className="status-card__message">{resendMessage}</p> : null}
                </div>
              </WarningCard>
            ) : null}
            {errorMessage ? (
              <ErrorCard title={t("cards.errorTitle")} message={errorMessage} />
            ) : null}
            <Button type="submit" loading={submitting}>
              {t("login.submitIdle")}
            </Button>
          </form>
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
          {oauthProviders.length > 0 ? (
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
