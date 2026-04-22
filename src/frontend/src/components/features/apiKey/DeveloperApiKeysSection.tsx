import { Trash2 } from "lucide-react";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";

import type { APIKeyRecord } from "../../../hooks/api/apiKey/useApiKeyApi";
import {
    Button,
    CopyField,
    InlineMessage,
    InputField,
    Modal,
    ModalButton,
    StatusBadge,
    ToggleSwitch,
} from "../../ui";

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

type DeveloperApiKeyListProps = {
    items: APIKeyRecord[];
    toggleBusyId: number | null;
    onToggleStatus: (apiKeyId: number, enabled: boolean) => void;
    onRequestDelete: (item: APIKeyRecord) => void;
    t: TFunction;
};

function DeveloperApiKeyList({
    items,
    toggleBusyId,
    onToggleStatus,
    onRequestDelete,
    t,
}: DeveloperApiKeyListProps) {
    return (
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
                                <p>
                                    {t("settings.developers.meta.accessKey")}: {item.key_prefix}
                                    ...
                                </p>
                            </div>
                            <div className="developer-key-card__controls">
                                <ToggleSwitch
                                    checked={isActive}
                                    disabled={toggleBusyId === item.id}
                                    onCheckedChange={(nextChecked) => {
                                        onToggleStatus(item.id, nextChecked);
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
                            <Button
                                type="button"
                                className="developer-delete-inline-btn"
                                aria-label={t("settings.developers.actions.delete")}
                                onClick={() => {
                                    onRequestDelete(item);
                                }}
                            >
                                <Trash2 />
                                <span>{t("settings.developers.actions.delete")}</span>
                            </Button>
                        </div>
                    </article>
                );
            })}
        </div>
    );
}

type CreateApiKeyModalProps = {
    open: boolean;
    apiKeyName: string;
    busy: boolean;
    errorMessage: string | null;
    onNameChange: (value: string) => void;
    onClose: () => void;
    onSubmit: () => void;
    t: TFunction;
};

function CreateApiKeyModal({
    open,
    apiKeyName,
    busy,
    errorMessage,
    onNameChange,
    onClose,
    onSubmit,
    t,
}: CreateApiKeyModalProps) {
    return (
        <Modal
            open={open}
            title={t("settings.developers.createModal.title")}
            description={t("settings.developers.createModal.description")}
            onClose={onClose}
            footer={
                <>
                    <ModalButton variant="cancel" onClick={onClose}>
                        {t("settings.developers.actions.cancel")}
                    </ModalButton>
                    <ModalButton
                        variant="save"
                        disabled={!apiKeyName.trim() || busy}
                        loading={busy}
                        onClick={onSubmit}
                    >
                        {t("settings.developers.actions.save")}
                    </ModalButton>
                </>
            }
        >
            {errorMessage ? <InlineMessage>{errorMessage}</InlineMessage> : null}
            <InputField
                label={t("settings.developers.createModal.nameLabel")}
                value={apiKeyName}
                onValueChange={onNameChange}
                placeholder={t("settings.developers.createModal.namePlaceholder")}
            />
        </Modal>
    );
}

type CreatedSecretModalProps = {
    secret: string | null;
    copied: boolean;
    onCopy: () => void;
    onClose: () => void;
    t: TFunction;
};

function CreatedSecretModal({ secret, copied, onCopy, onClose, t }: CreatedSecretModalProps) {
    return (
        <Modal
            open={Boolean(secret)}
            title={t("settings.developers.revealModal.title")}
            description={t("settings.developers.revealModal.description")}
            onClose={onClose}
            footer={
                <ModalButton variant="close" onClick={onClose}>
                    {t("settings.developers.actions.close")}
                </ModalButton>
            }
        >
            <CopyField
                value={secret ?? ""}
                inputAriaLabel={t("settings.developers.revealModal.title")}
                copyLabel={t("settings.developers.revealModal.copy")}
                copiedLabel={t("settings.developers.revealModal.copied")}
                copied={copied}
                disabled={!secret}
                onCopy={onCopy}
            />
        </Modal>
    );
}

type DeleteApiKeyModalProps = {
    target: APIKeyRecord | null;
    busy: boolean;
    onClose: () => void;
    onConfirmDelete: () => void;
    t: TFunction;
};

function DeleteApiKeyModal({ target, busy, onClose, onConfirmDelete, t }: DeleteApiKeyModalProps) {
    return (
        <Modal
            open={Boolean(target)}
            title={t("settings.developers.deactivateModal.title")}
            description={t("settings.developers.deactivateModal.description")}
            onClose={onClose}
            footer={
                <>
                    <ModalButton variant="cancel" onClick={onClose}>
                        {t("settings.developers.actions.cancel")}
                    </ModalButton>
                    <ModalButton variant="danger" loading={busy} onClick={onConfirmDelete}>
                        {t("settings.developers.actions.delete")}
                    </ModalButton>
                </>
            }
        />
    );
}

type DeveloperApiKeysSectionProps = {
    controller: {
        items: APIKeyRecord[];
        loading: boolean;
        errorMessage: string | null;
        createModalOpen: boolean;
        newApiKeyName: string;
        createBusy: boolean;
        createErrorMessage: string | null;
        createdSecret: string | null;
        copied: boolean;
        deactivateTarget: APIKeyRecord | null;
        deactivateBusy: boolean;
        toggleBusyId: number | null;
        setNewApiKeyName: (value: string) => void;
        openCreateModal: () => void;
        closeCreateModal: () => void;
        handleCreateApiKey: () => void;
        handleToggleStatus: (apiKeyId: number, enabled: boolean) => void;
        setDeactivateTarget: (item: APIKeyRecord | null) => void;
        closeDeleteModal: () => void;
        confirmDelete: () => void;
        closeSecretModal: () => void;
        copySecret: () => void;
    };
};

export function DeveloperApiKeysSection({ controller }: DeveloperApiKeysSectionProps) {
    const { t } = useTranslation();

    return (
        <section className="developer-section" aria-label={t("settings.developers.title")}>
            <div className="developer-section__actions">
                <ModalButton variant="save" onClick={controller.openCreateModal}>
                    {t("settings.developers.createButton")}
                </ModalButton>
            </div>

            {controller.errorMessage ? (
                <InlineMessage>{controller.errorMessage}</InlineMessage>
            ) : null}

            {controller.loading ? (
                <p className="developer-section__loading">{t("settings.developers.loading")}</p>
            ) : controller.items.length === 0 ? (
                <p className="developer-section__loading">{t("settings.developers.empty")}</p>
            ) : (
                <DeveloperApiKeyList
                    items={controller.items}
                    toggleBusyId={controller.toggleBusyId}
                    onToggleStatus={controller.handleToggleStatus}
                    onRequestDelete={controller.setDeactivateTarget}
                    t={t}
                />
            )}

            <CreateApiKeyModal
                open={controller.createModalOpen}
                apiKeyName={controller.newApiKeyName}
                busy={controller.createBusy}
                errorMessage={controller.createErrorMessage}
                onNameChange={controller.setNewApiKeyName}
                onClose={controller.closeCreateModal}
                onSubmit={controller.handleCreateApiKey}
                t={t}
            />
            <CreatedSecretModal
                secret={controller.createdSecret}
                copied={controller.copied}
                onCopy={controller.copySecret}
                onClose={controller.closeSecretModal}
                t={t}
            />
            <DeleteApiKeyModal
                target={controller.deactivateTarget}
                busy={controller.deactivateBusy}
                onClose={controller.closeDeleteModal}
                onConfirmDelete={controller.confirmDelete}
                t={t}
            />
        </section>
    );
}
