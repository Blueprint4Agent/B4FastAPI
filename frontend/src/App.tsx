import { Navigate, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuthContext } from "./hooks/useAuth";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuthContext();
  const { t } = useTranslation();

  if (loading) {
    return <main className="panel">{t("app.loadingSession")}</main>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
