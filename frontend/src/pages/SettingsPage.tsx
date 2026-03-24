import { useEffect, useState } from "react";
import { SlidersHorizontal, UserRound } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button, InputField, MenuList, PrimaryCard } from "../components/ui";
import { ErrorCard, InfoCard } from "../components/StatusCard";
import { useAuthContext } from "../hooks/useAuth";
import { extractApiDetail, resolveAuthErrorMessage } from "../utils/authError";

type SaveFeedback = {
    message: string;
    tone: "error" | "info";
} | null;
type SettingsMenuKey = "profile" | "general";

export function SettingsPage() {
    const { t } = useTranslation();
    const { user, updateProfileName } = useAuthContext();
    const [activeMenu, setActiveMenu] = useState<SettingsMenuKey>("profile");
    const [nameInput, setNameInput] = useState("");
    const [saveBusy, setSaveBusy] = useState(false);
    const [saveFeedback, setSaveFeedback] = useState<SaveFeedback>(null);

    const showProfile = activeMenu === "profile";
    const HeaderIcon = showProfile ? UserRound : SlidersHorizontal;
    const settingsMenuItems = [
        { key: "profile", label: t("settings.menu.profile"), icon: UserRound },
        { key: "general", label: t("settings.menu.general"), icon: SlidersHorizontal },
    ] as const;
    const normalizedNameInput = nameInput.trim();
    const normalizedCurrentName = (user?.name ?? "").trim();
    const isNameChanged = normalizedNameInput !== normalizedCurrentName;

    useEffect(() => {
        setNameInput(user?.name ?? "");
    }, [user?.name]);

    useEffect(() => {
        setSaveFeedback(null);
        setNameInput(user?.name ?? "");
    }, [activeMenu]);

    const handleSaveName = async () => {
        const nextName = normalizedNameInput;
        if (!nextName || !isNameChanged) {
            return;
        }

        setSaveBusy(true);
        setSaveFeedback(null);
        try {
            await updateProfileName({ name: nextName });
            setSaveFeedback({
                tone: "info",
                message: t("settings.profile.saveSuccess"),
            });
        } catch (error) {
            const detail = extractApiDetail(error);
            setSaveFeedback({
                tone: "error",
                message: resolveAuthErrorMessage(t, detail, "settings.profile.saveError"),
            });
        } finally {
            setSaveBusy(false);
        }
    };

    return (
        <section className="settings-layout">
            <MenuList
                items={settingsMenuItems}
                activeKey={activeMenu}
                onSelect={setActiveMenu}
                ariaLabel={t("settings.menu.title")}
            />

            <PrimaryCard className="settings-content-card">
                {showProfile ? (
                    <>
                        <header className="settings-content-card__header">
                            <h1>
                                <span className="settings-content-card__title-icon" aria-hidden="true">
                                    <HeaderIcon />
                                </span>
                                <span>{t("settings.profile.title")}</span>
                            </h1>
                            <p>{t("settings.profile.subtitle")}</p>
                        </header>

                        <section className="settings-profile-content" aria-label={t("settings.profile.title")}>
                            <div className="settings-profile-info">
                                <article className="settings-profile-field-card">
                                    <h2>{t("settings.labels.name")}</h2>
                                    <form
                                        className="settings-profile-name-edit"
                                        onSubmit={(event) => {
                                            event.preventDefault();
                                            void handleSaveName();
                                        }}
                                    >
                                        <InputField
                                            className="settings-profile-name-input"
                                            label=""
                                            value={nameInput}
                                            onValueChange={(value) => {
                                                setNameInput(value);
                                                if (saveFeedback) {
                                                    setSaveFeedback(null);
                                                }
                                            }}
                                            placeholder={t("settings.profile.namePlaceholder")}
                                            aria-label={t("settings.labels.name")}
                                        />
                                        <Button
                                            className="settings-profile-save-button"
                                            type="submit"
                                            loading={saveBusy}
                                            disabled={!isNameChanged}
                                        >
                                            {t("settings.profile.save")}
                                        </Button>
                                    </form>

                                    {saveFeedback?.tone === "info" ? (
                                        <div className="settings-feedback">
                                            <InfoCard
                                                title={t("cards.infoTitle")}
                                                message={saveFeedback.message}
                                            />
                                        </div>
                                    ) : null}
                                    {saveFeedback?.tone === "error" ? (
                                        <div className="settings-feedback">
                                            <ErrorCard
                                                title={t("cards.errorTitle")}
                                                message={saveFeedback.message}
                                            />
                                        </div>
                                    ) : null}
                                </article>

                                <article className="settings-profile-field-card">
                                    <h2>{t("settings.labels.email")}</h2>
                                    <p>{user?.email ?? "-"}</p>
                                </article>
                            </div>

                            <aside className="settings-profile-photo-panel">
                                <h2>{t("settings.profile.photo")}</h2>
                                <div className="settings-profile-photo-card__preview" aria-hidden="true">
                                    {user?.name?.slice(0, 1).toUpperCase() ?? "U"}
                                </div>
                            </aside>
                        </section>
                    </>
                ) : (
                    <>
                        <header className="settings-content-card__header">
                            <h1>
                                <span className="settings-content-card__title-icon" aria-hidden="true">
                                    <HeaderIcon />
                                </span>
                                <span>{t("settings.general.title")}</span>
                            </h1>
                            <p>{t("settings.general.subtitle")}</p>
                        </header>
                        <p className="settings-content-card__placeholder">
                            {t("settings.general.placeholder")}
                        </p>
                    </>
                )}
            </PrimaryCard>
        </section>
    );
}

