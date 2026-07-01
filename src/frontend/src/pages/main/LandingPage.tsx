import { ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BrandMark, Button } from "../../components/ui";
import { startDesktopWindowDrag } from "../../utils/desktopWindow";
import { markLandingStarted } from "../../utils/landing";

type LandingPageProps = {
    loginEnabled: boolean;
};

export function LandingPage({ loginEnabled }: LandingPageProps) {
    const { t } = useTranslation();
    const navigate = useNavigate();

    return (
        <div className="landing-shell">
            <header
                className="landing-nav"
                aria-label={t("landing.navAria")}
                data-tauri-drag-region
                onMouseDown={startDesktopWindowDrag}
            >
                <div className="landing-nav__brand" data-tauri-drag-region>
                    <BrandMark className="brand-mark--nav" />
                </div>
            </header>
            <main className="landing-page">
                <section className="landing-hero" aria-labelledby="landing-title">
                    <div className="landing-hero__banner-icon" aria-hidden="true">
                        <BrandMark />
                    </div>
                    <p className="landing-hero__eyebrow">{t("landing.eyebrow")}</p>
                    <h1 id="landing-title">{t("landing.title")}</h1>
                    <p className="landing-hero__subtitle">{t("landing.subtitle")}</p>
                    <p className="landing-hero__note">{t("landing.note")}</p>

                    <Button
                        className="landing-hero__start-button"
                        onClick={() => {
                            markLandingStarted();
                            navigate(loginEnabled ? "/login" : "/show-case");
                        }}
                    >
                        <span className="landing-hero__button-label">{t("landing.start")}</span>
                        <ArrowRight aria-hidden="true" />
                    </Button>
                </section>
            </main>
        </div>
    );
}
