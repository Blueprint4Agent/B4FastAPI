import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AppNavbar } from "./components/AppNavbar";
import { useAuthContext } from "./hooks/useAuth";
import { DashboardPage } from "./pages/DashboardPage";
import { ForgotPasswordEmailSentPage } from "./pages/ForgotPasswordEmailSentPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { ResetPasswordSuccessPage } from "./pages/ResetPasswordSuccessPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignupEmailSentPage } from "./pages/SignupEmailSentPage";
import { SignupPage } from "./pages/SignupPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function ProtectedLayout() {
  const { user, loading } = useAuthContext();
  const { t } = useTranslation();

  if (loading) {
    return (
      <main className="page">
        <section className="panel">{t("app.loadingSession")}</section>
      </main>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-shell">
      <AppNavbar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/signup/email-sent" element={<SignupEmailSentPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/forgot-password/email-sent" element={<ForgotPasswordEmailSentPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/reset-password/success" element={<ResetPasswordSuccessPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
