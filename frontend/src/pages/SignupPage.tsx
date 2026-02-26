import { FormEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { ErrorCard, WarningCard } from "../components/StatusCard";
import { ThemeToggle } from "../components/ThemeToggle";
import {
  Button,
  InputField,
  PanelCard,
  ValidationCard,
  type ValidationRule
} from "../components/ui";
import { useAuthContext } from "../hooks/useAuth";
import { isValidEmail, isValidPassword } from "../utils/validation";

type APIError = {
  detail?: {
    error?: string;
    message?: string;
  };
};

function extractApiDetail(error: unknown): APIError["detail"] | null {
  if (!error || typeof error !== "object") return null;
  const detail = (error as APIError).detail;
  if (!detail || typeof detail !== "object") return null;
  return detail;
}

export function SignupPage() {
  const { t } = useTranslation();
  const { signup } = useAuthContext();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [warningMessage, setWarningMessage] = useState("");

  const passwordMismatch = confirmPassword.length > 0 && confirmPassword !== password;
  const hasFeedback = useMemo(
    () => Boolean(errorMessage || warningMessage),
    [errorMessage, warningMessage]
  );
  const emailRules = useMemo<ValidationRule[]>(
    () => [
      {
        label: t("signup.rules.email.format"),
        isValid: isValidEmail(email)
      }
    ],
    [email, t]
  );
  const passwordRules = useMemo<ValidationRule[]>(
    () => [
      {
        label: t("signup.rules.password.length"),
        isValid: password.length >= 8 && password.length <= 24
      },
      {
        label: t("signup.rules.password.upper"),
        isValid: /[A-Z]/.test(password)
      },
      {
        label: t("signup.rules.password.number"),
        isValid: /\d/.test(password)
      },
      {
        label: t("signup.rules.password.symbol"),
        isValid: /[^A-Za-z0-9]/.test(password)
      },
      {
        label: t("signup.rules.password.noSpace"),
        isValid: !/\s/.test(password) && password.length > 0
      }
    ],
    [password, t]
  );
  const confirmRules = useMemo<ValidationRule[]>(
    () => [
      {
        label: t("signup.rules.confirm.match"),
        isValid: confirmPassword.length > 0 && !passwordMismatch
      }
    ],
    [confirmPassword.length, passwordMismatch, t]
  );

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage("");
    setWarningMessage("");

    if (!name.trim()) {
      setWarningMessage(t("auth.errors.requiredName"));
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
    if (!confirmPassword.trim()) {
      setWarningMessage(t("auth.errors.requiredConfirmPassword"));
      setSubmitting(false);
      return;
    }
    if (passwordMismatch) {
      setWarningMessage(t("auth.errors.passwordMismatch"));
      setSubmitting(false);
      return;
    }

    try {
      await signup({ name, email, password });
      navigate("/login", { replace: true });
    } catch (nextError) {
      const detail = extractApiDetail(nextError);
      setErrorMessage(detail?.message || detail?.error || t("auth.errors.signupFallback"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="page">
      <ThemeToggle />
      <PanelCard title={t("signup.title")} subtitle={t("signup.subtitle")}>
        <form onSubmit={onSubmit} className="form" noValidate>
          <InputField
            label={t("signup.fields.name")}
            type="text"
            autoComplete="name"
            minLength={2}
            maxLength={50}
            value={name}
            onValueChange={setName}
          />
          <InputField
            label={t("signup.fields.email")}
            type="email"
            autoComplete="email"
            value={email}
            onValueChange={setEmail}
          />
          <ValidationCard title={t("signup.validation.email")} rules={emailRules} />
          <InputField
            label={t("signup.fields.password")}
            type="password"
            autoComplete="new-password"
            value={password}
            onValueChange={setPassword}
          />
          <ValidationCard title={t("signup.validation.password")} rules={passwordRules} />
          <InputField
            label={t("signup.fields.confirmPassword")}
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onValueChange={setConfirmPassword}
          />
          <ValidationCard title={t("signup.validation.confirm")} rules={confirmRules} />
          {hasFeedback && warningMessage ? (
            <WarningCard title={t("cards.warningTitle")} message={warningMessage} />
          ) : null}
          {hasFeedback && errorMessage ? (
            <ErrorCard title={t("cards.errorTitle")} message={errorMessage} />
          ) : null}
          <Button type="submit" disabled={submitting || passwordMismatch}>
            {submitting ? t("signup.submitBusy") : t("signup.submitIdle")}
          </Button>
        </form>
        <p className="muted auth-footer">
          {t("signup.loginPrompt")}{" "}
          <Link to="/login" className="text-link">
            {t("signup.loginLink")}
          </Link>
        </p>
      </PanelCard>
    </main>
  );
}
