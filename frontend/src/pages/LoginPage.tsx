import { FormEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { ErrorCard, WarningCard } from "../components/StatusCard";
import { ThemeToggle } from "../components/ThemeToggle";
import { BrandMark, Button, FormCheckbox, InputField, PanelCard } from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";
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

function extractApiDetail(error: unknown): APIError["detail"] | null {
  if (!error || typeof error !== "object") return null;
  const detail = (error as APIError).detail;
  if (!detail || typeof detail !== "object") return null;
  return detail;
}

export function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuthContext();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [warningMessage, setWarningMessage] = useState("");

  const hasFeedback = useMemo(
    () => Boolean(errorMessage || warningMessage),
    [errorMessage, warningMessage]
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage("");
    setWarningMessage("");

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
      } else {
        setErrorMessage(detail?.message || detail?.error || t("auth.errors.loginFallback"));
      }
    } finally {
      setSubmitting(false);
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
            <FormCheckbox
              checked={rememberMe}
              onCheckedChange={setRememberMe}
              label={t("login.rememberMe")}
            />
            {hasFeedback && warningMessage ? (
              <WarningCard title={t("cards.warningTitle")} message={warningMessage} />
            ) : null}
            {hasFeedback && errorMessage ? (
              <ErrorCard title={t("cards.errorTitle")} message={errorMessage} />
            ) : null}
            <Button type="submit" disabled={submitting}>
              {submitting ? t("login.submitBusy") : t("login.submitIdle")}
            </Button>
          </form>
          <p className="muted auth-footer">
            {t("login.signupPrompt")}{" "}
            <Link to="/signup" className="text-link">
              {t("login.signupLink")}
            </Link>
          </p>
        </PanelCard>
      </div>
    </main>
  );
}
