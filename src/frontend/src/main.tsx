import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { DesktopTitleBar } from "./components/layout/DesktopTitleBar";
import { AuthProvider } from "./hooks/useAuth";
import { initializeDesktopRuntime } from "./utils/desktopRuntime";
import "./i18n";
import "./styles/app.css";

initializeDesktopRuntime();

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <BrowserRouter>
            <DesktopTitleBar />
            <AuthProvider>
                <App />
            </AuthProvider>
        </BrowserRouter>
    </React.StrictMode>,
);
