import { useTranslation } from "react-i18next";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AppNavbar } from "./components/AppNavbar";
import { useAuthContext } from "./hooks/useAuth";
import { useAppConfig } from "./hooks/useFeatures";
import { useTheme } from "./hooks/useTheme";
import { ForgotPasswordEmailSentPage } from "./pages/ForgotPasswordEmailSentPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoadingPage } from "./pages/LoadingPage";
import { LoginPage } from "./pages/LoginPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { ResetPasswordSuccessPage } from "./pages/ResetPasswordSuccessPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ShowCaseNotFoundPage } from "./pages/ShowCaseNotFoundPage";
import { ShowCasePage } from "./pages/ShowCasePage";
import { SignupEmailSentPage } from "./pages/SignupEmailSentPage";
import { SignupPage } from "./pages/SignupPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function ProtectedLayout({
    loginEnabled,
    configLoading,
}: {
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();
    const { t } = useTranslation();

    if (loading || configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }
    if (loginEnabled && !user) {
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

function NotFoundRoute({
    loginEnabled,
    configLoading,
}: {
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();

    if (loading || configLoading) {
        return <LoadingPage />;
    }

    if (user || !loginEnabled) {
        return (
            <div className="app-shell">
                <AppNavbar />
                <main className="app-main">
                    <ShowCaseNotFoundPage />
                </main>
            </div>
        );
    }

    return (
        <main className="page">
            <ShowCaseNotFoundPage />
        </main>
    );
}

export function App() {
    useTheme();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const loginEnabled = appConfig?.login_enabled !== false;

    return (
        <Routes>
            <Route path="/" element={<Navigate to="/show-case" replace />} />
            <Route
                path="/login"
                element={loginEnabled ? <LoginPage /> : <Navigate to="/show-case" replace />}
            />
            <Route path="/loading" element={<LoadingPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/signup/email-sent" element={<SignupEmailSentPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/forgot-password/email-sent" element={<ForgotPasswordEmailSentPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/reset-password/success" element={<ResetPasswordSuccessPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route
                element={
                    <ProtectedLayout loginEnabled={loginEnabled} configLoading={configLoading} />
                }
            >
                <Route path="/dashboard" element={<Navigate to="/show-case" replace />} />
                <Route path="/show-case" element={<ShowCasePage />} />
                <Route
                    path="/show-case/loading"
                    element={<LoadingPage message="Loading preview..." />}
                />
                <Route path="/show-case/404" element={<ShowCaseNotFoundPage />} />
                <Route path="/settings" element={<SettingsPage />} />
            </Route>
            <Route
                path="*"
                element={
                    <NotFoundRoute loginEnabled={loginEnabled} configLoading={configLoading} />
                }
            />
        </Routes>
    );
}
