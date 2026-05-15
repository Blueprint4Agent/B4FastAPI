import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { AppNavbar } from "./components/layout/AppNavbar";
import { AppSidebar } from "./components/layout/AppSidebar";
import { useAuthContext } from "./hooks/useAuth";
import { useAppConfig } from "./hooks/useFeatures";
import { useTheme } from "./hooks/useTheme";
import { hasStartedFromLanding } from "./utils/landing";
import { ForgotPasswordEmailSentPage } from "./pages/login/ForgotPasswordEmailSentPage";
import { ForgotPasswordPage } from "./pages/login/ForgotPasswordPage";
import { LoginPage } from "./pages/login/LoginPage";
import { ResetPasswordPage } from "./pages/login/ResetPasswordPage";
import { ResetPasswordSuccessPage } from "./pages/login/ResetPasswordSuccessPage";
import { SignupEmailSentPage } from "./pages/login/SignupEmailSentPage";
import { SignupPage } from "./pages/login/SignupPage";
import { VerifyEmailPage } from "./pages/login/VerifyEmailPage";
import { LoadingPage } from "./pages/main/LoadingPage";
import { LandingPage } from "./pages/main/LandingPage";
import { ShowCaseNotFoundPage } from "./pages/main/ShowCaseNotFoundPage";
import { ShowCasePage } from "./pages/main/ShowCasePage";
import { SettingsPage } from "./pages/settings/SettingsPage";

function ProtectedLayout({
    loginEnabled,
    configLoading,
}: {
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();
    const { t } = useTranslation();
    const location = useLocation();
    const isMainPage = location.pathname === "/show-case";
    const [sidebarExpanded, setSidebarExpanded] = useState(false);

    useEffect(() => {
        if (!isMainPage) {
            setSidebarExpanded(false);
        }
    }, [isMainPage]);

    if (loading || configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }
    if (loginEnabled && !user) {
        return <Navigate to="/login" replace />;
    }

    const mainClassName = isMainPage
        ? sidebarExpanded
            ? "app-main app-main--with-sidebar app-main--sidebar-expanded"
            : "app-main app-main--with-sidebar app-main--sidebar-collapsed"
        : "app-main";

    return (
        <div className="app-shell">
            <AppNavbar />
            <div className="app-body">
                {isMainPage ? (
                    <AppSidebar
                        expanded={sidebarExpanded}
                        onToggleExpanded={() => {
                            setSidebarExpanded((prev) => !prev);
                        }}
                    />
                ) : null}
                <main className={mainClassName}>
                    <Outlet />
                </main>
            </div>
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
    const { t } = useTranslation();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const loginEnabled = appConfig?.login_enabled === true;
    const landingStarted = hasStartedFromLanding();

    if (configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }

    return (
        <Routes>
            <Route
                path="/"
                element={
                    landingStarted ? (
                        <Navigate to={loginEnabled ? "/login" : "/show-case"} replace />
                    ) : (
                        <LandingPage loginEnabled={loginEnabled} />
                    )
                }
            />
            <Route
                path="/login"
                element={loginEnabled ? <LoginPage /> : <Navigate to="/show-case" replace />}
            />
            <Route path="/loading" element={<LoadingPage />} />
            <Route
                path="/signup"
                element={loginEnabled ? <SignupPage /> : <Navigate to="/show-case" replace />}
            />
            <Route
                path="/signup/email-sent"
                element={
                    loginEnabled ? <SignupEmailSentPage /> : <Navigate to="/show-case" replace />
                }
            />
            <Route
                path="/forgot-password"
                element={
                    loginEnabled ? <ForgotPasswordPage /> : <Navigate to="/show-case" replace />
                }
            />
            <Route
                path="/forgot-password/email-sent"
                element={
                    loginEnabled ? (
                        <ForgotPasswordEmailSentPage />
                    ) : (
                        <Navigate to="/show-case" replace />
                    )
                }
            />
            <Route
                path="/reset-password"
                element={
                    loginEnabled ? <ResetPasswordPage /> : <Navigate to="/show-case" replace />
                }
            />
            <Route
                path="/reset-password/success"
                element={
                    loginEnabled ? (
                        <ResetPasswordSuccessPage />
                    ) : (
                        <Navigate to="/show-case" replace />
                    )
                }
            />
            <Route
                path="/verify-email"
                element={loginEnabled ? <VerifyEmailPage /> : <Navigate to="/show-case" replace />}
            />
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
