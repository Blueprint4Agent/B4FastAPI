import { Check, Copy, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { APIKeyRecord } from "../api/authApi";
import { createApiKey, deleteApiKey, listApiKeys, updateApiKeyStatus } from "../api/authApi";
import { InlineMessage, InputField, Modal, ModalButton, StatusBadge, ToggleSwitch } from "./ui";

function formatDateTime(value: string | null | undefined): string {
    if (!value) {
        return "-";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "-";
    }

    return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
    }).format(date);
}

export function DeveloperApiKeysSection() {
    const { t } = useTranslation();
    const [items, setItems] = useState<APIKeyRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [newApiKeyName, setNewApiKeyName] = useState("");
    const [createBusy, setCreateBusy] = useState(false);
    const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
    const [createdSecret, setCreatedSecret] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const [deactivateTarget, setDeactivateTarget] = useState<APIKeyRecord | null>(null);
    const [deactivateBusy, setDeactivateBusy] = useState(false);
    const [toggleBusyId, setToggleBusyId] = useState<number | null>(null);

    const loadApiKeys = async () => {
        setLoading(true);
        setErrorMessage(null);
        try {
            const response = await listApiKeys();
            setItems(response.items);
        } catch {
            setErrorMessage(t("settings.developers.listLoadError"));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadApiKeys();
    }, []);

    return (
        <section className="developer-section" aria-label={t("settings.developers.title")}>
            <div className="developer-section__actions">
                <ModalButton
                    variant="save"
                    onClick={() => {
                        setCreateModalOpen(true);
                        setCreateErrorMessage(null);
                    }}
                >
                    {t("settings.developers.createButton")}
                </ModalButton>
            </div>

            {errorMessage ? <InlineMessage>{errorMessage}</InlineMessage> : null}

            {loading ? (
                <p className="developer-section__loading">{t("settings.developers.loading")}</p>
            ) : items.length === 0 ? (
                <p className="developer-section__loading">{t("settings.developers.empty")}</p>
            ) : (
                <div className="developer-key-list">
                    {items.map((item) => {
                        const isActive = !item.revoked_at;
                        return (
                            <article key={item.id} className="developer-key-card">
                                <div className="developer-key-card__top">
                                    <div className="developer-key-card__identity">
                                        <div className="developer-key-card__title-row">
                                            <h3>{item.name}</h3>
                                            <StatusBadge tone={isActive ? "active" : "inactive"}>
                                                {isActive
                                                    ? t("settings.developers.status.active")
                                                    : t("settings.developers.status.inactive")}
                                            </StatusBadge>
                                        </div>
                                        <p>Access key: {item.key_prefix}...</p>
                                    </div>
                                    <div className="developer-key-card__controls">
                                        <ToggleSwitch
                                            checked={isActive}
                                            disabled={toggleBusyId === item.id}
                                            onCheckedChange={(nextChecked) => {
                                                setToggleBusyId(item.id);
                                                setErrorMessage(null);
                                                void updateApiKeyStatus(item.id, nextChecked)
                                                    .then((updated) => {
                                                        setItems((prev) =>
                                                            prev.map((row) =>
                                                                row.id === updated.id
                                                                    ? updated
                                                                    : row,
                                                            ),
                                                        );
                                                    })
                                                    .catch(() => {
                                                        setErrorMessage(
                                                            t(
                                                                "settings.developers.deactivateError",
                                                            ),
                                                        );
                                                    })
                                                    .finally(() => {
                                                        setToggleBusyId(null);
                                                    });
                                            }}
                                            label={t("settings.developers.columns.enabled")}
                                        />
                                    </div>
                                </div>
                                <div className="developer-key-card__meta">
                                    <span>{t("settings.developers.meta.requestCount")}: -</span>
                                    <span>
                                        {t("settings.developers.meta.created")}:{" "}
                                        {formatDateTime(item.created_at)}
                                    </span>
                                    <span>
                                        {t("settings.developers.meta.lastUsed")}:{" "}
                                        {formatDateTime(item.last_used_at)}
                                    </span>
                                    <button
                                        type="button"
                                        className="developer-delete-inline-btn"
                                        aria-label={t("settings.developers.actions.delete")}
                                        onClick={() => {
                                            setDeactivateTarget(item);
                                        }}
                                    >
                                        <Trash2 />
                                        <span>{t("settings.developers.actions.delete")}</span>
                                    </button>
                                </div>
                            </article>
                        );
                    })}
                </div>
            )}

            <Modal
                open={createModalOpen}
                title={t("settings.developers.createModal.title")}
                description={t("settings.developers.createModal.description")}
                onClose={() => {
                    if (createBusy) {
                        return;
                    }
                    setCreateModalOpen(false);
                    setNewApiKeyName("");
                    setCreateErrorMessage(null);
                }}
                footer={
                    <>
                        <ModalButton
                            variant="cancel"
                            onClick={() => {
                                if (createBusy) {
                                    return;
                                }
                                setCreateModalOpen(false);
                                setNewApiKeyName("");
                                setCreateErrorMessage(null);
                            }}
                        >
                            {t("settings.developers.actions.cancel")}
                        </ModalButton>
                        <ModalButton
                            variant="save"
                            disabled={!newApiKeyName.trim() || createBusy}
                            loading={createBusy}
                            onClick={() => {
                                setCreateBusy(true);
                                setCreateErrorMessage(null);
                                void createApiKey(newApiKeyName.trim())
                                    .then((result) => {
                                        setItems((prev) => [result.key, ...prev]);
                                        setCreateModalOpen(false);
                                        setNewApiKeyName("");
                                        setCreateErrorMessage(null);
                                        setCreatedSecret(result.api_key);
                                        setCopied(false);
                                    })
                                    .catch(() => {
                                        setCreateErrorMessage(t("settings.developers.createError"));
                                    })
                                    .finally(() => {
                                        setCreateBusy(false);
                                    });
                            }}
                        >
                            {t("settings.developers.actions.save")}
                        </ModalButton>
                    </>
                }
            >
                {createErrorMessage ? <InlineMessage>{createErrorMessage}</InlineMessage> : null}
                <InputField
                    label={t("settings.developers.createModal.nameLabel")}
                    value={newApiKeyName}
                    onValueChange={setNewApiKeyName}
                    placeholder={t("settings.developers.createModal.namePlaceholder")}
                />
            </Modal>

            <Modal
                open={Boolean(createdSecret)}
                title={t("settings.developers.revealModal.title")}
                description={t("settings.developers.revealModal.description")}
                onClose={() => {
                    setCreatedSecret(null);
                    setCopied(false);
                }}
                footer={
                    <ModalButton
                        variant="close"
                        onClick={() => {
                            setCreatedSecret(null);
                            setCopied(false);
                        }}
                    >
                        {t("settings.developers.actions.close")}
                    </ModalButton>
                }
            >
                <div className="developer-section__secret-wrap">
                    <input
                        type="text"
                        readOnly
                        value={createdSecret ?? ""}
                        className="developer-section__secret-input"
                        aria-label={t("settings.developers.revealModal.title")}
                    />
                    <button
                        type="button"
                        className="developer-section__secret-copy-btn"
                        aria-label={
                            copied
                                ? t("settings.developers.revealModal.copied")
                                : t("settings.developers.revealModal.copy")
                        }
                        onClick={() => {
                            if (!createdSecret) {
                                return;
                            }
                            void navigator.clipboard.writeText(createdSecret).then(() => {
                                setCopied(true);
                            });
                        }}
                    >
                        {copied ? <Check /> : <Copy />}
                    </button>
                </div>
            </Modal>

            <Modal
                open={Boolean(deactivateTarget)}
                title={t("settings.developers.deactivateModal.title")}
                description="Are you sure you want to delete this API key?"
                onClose={() => {
                    if (deactivateBusy) {
                        return;
                    }
                    setDeactivateTarget(null);
                }}
                footer={
                    <>
                        <ModalButton
                            variant="cancel"
                            onClick={() => {
                                if (deactivateBusy) {
                                    return;
                                }
                                setDeactivateTarget(null);
                            }}
                        >
                            {t("settings.developers.actions.cancel")}
                        </ModalButton>
                        <ModalButton
                            variant="danger"
                            loading={deactivateBusy}
                            onClick={() => {
                                if (!deactivateTarget) {
                                    return;
                                }
                                setDeactivateBusy(true);
                                setErrorMessage(null);
                                void deleteApiKey(deactivateTarget.id)
                                    .then((deleted) => {
                                        setItems((prev) =>
                                            prev.filter((item) => item.id !== deleted.id),
                                        );
                                        setDeactivateTarget(null);
                                    })
                                    .catch(() => {
                                        setErrorMessage(t("settings.developers.deactivateError"));
                                    })
                                    .finally(() => {
                                        setDeactivateBusy(false);
                                    });
                            }}
                        >
                            {t("settings.developers.actions.delete")}
                        </ModalButton>
                    </>
                }
            />
        </section>
    );
}
