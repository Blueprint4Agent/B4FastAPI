import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsPage } from "../../../../pages/settings/SettingsPage";
import { FULL_SYSTEM_SCENARIO } from "../../../fixtures/fullSystemScenarioData";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const createApiKeyMock = vi.fn();
const deleteApiKeyMock = vi.fn();
const listApiKeysMock = vi.fn();
const updateApiKeyStatusMock = vi.fn();
const updateProfileMock = vi.fn();
let mockedApiKeyItems: Array<{
    id: number;
    name: string;
    key_prefix: string;
    created_at: string;
    last_used_at: string | null;
    revoked_at: string | null;
}> = [];

const apiKeyErrorMessageByCode: Record<string, string> = {
    API_KEY_NAME_ALREADY_EXISTS: "An API key with this name already exists.",
    API_KEY_NOT_FOUND: "The requested API key does not exist.",
};

const extractAPIKeyErrorDetailMock = (error: unknown) => {
    if (!error || typeof error !== "object") {
        return null;
    }
    const detail = (error as { detail?: unknown }).detail;
    return detail && typeof detail === "object"
        ? (detail as { error?: string; message?: string; details?: Record<string, unknown> })
        : null;
};

const resolveAPIKeyErrorMessageMock = (
    _t: unknown,
    detail: { error?: string; message?: string } | null,
    _fallbackKey: string,
) => {
    if (!detail?.error) {
        return detail?.message || "Failed to process API key request.";
    }
    return apiKeyErrorMessageByCode[detail.error] || detail.message || detail.error;
};

const apiKeyApiHookMock = {
    createApiKey: createApiKeyMock,
    deleteApiKey: deleteApiKeyMock,
    listApiKeys: listApiKeysMock,
    updateApiKeyStatus: updateApiKeyStatusMock,
    extractAPIKeyErrorDetail: extractAPIKeyErrorDetailMock,
    resolveAPIKeyErrorMessage: resolveAPIKeyErrorMessageMock,
};

vi.mock("../../../../hooks/useAuth", () => ({
    useAuthContext: () => ({
        user: FULL_SYSTEM_SCENARIO.principal,
        loading: false,
        login: vi.fn(),
        signup: vi.fn(),
        updateProfile: updateProfileMock,
        logout: vi.fn(),
        refreshSession: vi.fn(),
    }),
}));

vi.mock("../../../../hooks/useFeatures", () => ({
    useAppConfig: () => ({
        data: {
            login_enabled: true,
            email_enabled: false,
            oauth_enabled: false,
        },
        loading: false,
    }),
}));

vi.mock("../../../../hooks/api/apiKey/useApiKeyApi", () => ({
    useApiKeyApi: () => apiKeyApiHookMock,
}));

describe("SettingsPage developers scenario", () => {
    beforeEach(() => {
        createApiKeyMock.mockReset();
        deleteApiKeyMock.mockReset();
        listApiKeysMock.mockReset();
        updateApiKeyStatusMock.mockReset();
        updateProfileMock.mockReset();
        mockedApiKeyItems = [];

        listApiKeysMock.mockImplementation(async () => ({
            items: [...mockedApiKeyItems],
        }));
    });

    it("follows backend-aligned API key lifecycle flow from seeded principal context", async () => {
        // Given: seeded principal user and empty API key list.
        createApiKeyMock.mockImplementation(async () => {
            const created = {
                id: 101,
                name: FULL_SYSTEM_SCENARIO.apiKey.primaryName,
                key_prefix: "sk_live_abcd",
                created_at: "2026-04-30T12:00:00Z",
                last_used_at: null,
                revoked_at: null,
            };
            mockedApiKeyItems = [created, ...mockedApiKeyItems];
            return {
                api_key: `${FULL_SYSTEM_SCENARIO.apiKey.secretPrefix}primary_secret_001`,
                key: created,
            };
        });
        updateApiKeyStatusMock
            .mockResolvedValueOnce({
                id: 101,
                name: FULL_SYSTEM_SCENARIO.apiKey.primaryName,
                key_prefix: "sk_live_abcd",
                created_at: "2026-04-30T12:00:00Z",
                last_used_at: null,
                revoked_at: "2026-04-30T12:10:00Z",
            })
            .mockResolvedValueOnce({
                id: 101,
                name: FULL_SYSTEM_SCENARIO.apiKey.primaryName,
                key_prefix: "sk_live_abcd",
                created_at: "2026-04-30T12:00:00Z",
                last_used_at: null,
                revoked_at: null,
            });
        deleteApiKeyMock.mockImplementation(async (apiKeyId: number) => {
            mockedApiKeyItems = mockedApiKeyItems.filter((item) => item.id !== apiKeyId);
            return { id: apiKeyId };
        });

        renderWithRouter(<SettingsPage />, "/settings");
        const user = userEvent.setup();

        // When: user switches to developers section and creates key.
        await user.click(screen.getByRole("button", { name: "Developers" }));
        await user.click(screen.getByRole("button", { name: "Create API key" }));
        await user.type(
            screen.getByLabelText("API key name"),
            FULL_SYSTEM_SCENARIO.apiKey.primaryName,
        );
        await user.click(screen.getByRole("button", { name: "Save" }));

        // Then: key is created, reveal modal is shown once, and key appears in list.
        await waitFor(() => {
            expect(createApiKeyMock).toHaveBeenCalledWith(FULL_SYSTEM_SCENARIO.apiKey.primaryName);
        });
        expect(screen.getByRole("dialog", { name: "Copy API key now" })).toBeInTheDocument();
        expect(
            screen.getByDisplayValue(
                `${FULL_SYSTEM_SCENARIO.apiKey.secretPrefix}primary_secret_001`,
            ),
        ).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Close" }));
        await waitFor(() => {
            expect(screen.getByText(FULL_SYSTEM_SCENARIO.apiKey.primaryName)).toBeInTheDocument();
        });

        // When: key is disabled and then enabled again.
        await user.click(screen.getByRole("switch", { name: "Enabled" }));
        await waitFor(() => {
            expect(updateApiKeyStatusMock).toHaveBeenCalledWith(101, false);
        });
        await user.click(screen.getByRole("switch", { name: "Enabled" }));
        await waitFor(() => {
            expect(updateApiKeyStatusMock).toHaveBeenCalledWith(101, true);
        });

        // When: key delete is confirmed via modal.
        const apiKeyHeading = screen.getByText(FULL_SYSTEM_SCENARIO.apiKey.primaryName);
        const apiKeyCard = apiKeyHeading.closest("article");
        if (!apiKeyCard) {
            throw new Error("API key card element was not found.");
        }
        await user.click(within(apiKeyCard).getByRole("button", { name: "Delete" }));
        const deleteModal = screen.getByRole("dialog", { name: "Delete API key" });
        await user.click(within(deleteModal).getByRole("button", { name: "Delete" }));

        // Then: delete API call succeeds and key is removed from list.
        await waitFor(() => {
            expect(deleteApiKeyMock).toHaveBeenCalledWith(101);
        });
        await waitFor(() => {
            expect(
                screen.queryByText(FULL_SYSTEM_SCENARIO.apiKey.primaryName),
            ).not.toBeInTheDocument();
        });
    });

    it("shows backend-aligned conflict and not-found error branches", async () => {
        // Given: existing key in list and backend error branches for duplicate/not-found.
        mockedApiKeyItems = [
            {
                id: 201,
                name: FULL_SYSTEM_SCENARIO.apiKey.primaryName,
                key_prefix: "sk_live_abcd",
                created_at: "2026-04-30T12:00:00Z",
                last_used_at: null,
                revoked_at: null,
            },
        ];
        createApiKeyMock.mockRejectedValue({
            detail: {
                error: "API_KEY_NAME_ALREADY_EXISTS",
                message: "API key name already exists.",
            },
        });
        deleteApiKeyMock.mockRejectedValue({
            detail: {
                error: "API_KEY_NOT_FOUND",
                message: "API key not found.",
            },
        });

        renderWithRouter(<SettingsPage />, "/settings");
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Developers" }));

        // When: duplicate key name is created.
        await user.click(screen.getByRole("button", { name: "Create API key" }));
        await user.type(
            screen.getByLabelText("API key name"),
            FULL_SYSTEM_SCENARIO.apiKey.primaryName,
        );
        await user.click(screen.getByRole("button", { name: "Save" }));

        // Then: duplicate-name conflict message is shown.
        await waitFor(() => {
            expect(
                screen.getByText("An API key with this name already exists."),
            ).toBeInTheDocument();
        });

        // When: deleting an existing row returns not-found from backend.
        await user.click(screen.getByRole("button", { name: "Cancel" }));
        const existingHeading = screen.getByText(FULL_SYSTEM_SCENARIO.apiKey.primaryName);
        const existingCard = existingHeading.closest("article");
        if (!existingCard) {
            throw new Error("Existing API key card element was not found.");
        }
        await user.click(within(existingCard).getByRole("button", { name: "Delete" }));
        const deleteModal = screen.getByRole("dialog", { name: "Delete API key" });
        await user.click(within(deleteModal).getByRole("button", { name: "Delete" }));

        // Then: not-found branch keeps delete modal open after failed deletion call.
        await waitFor(() => {
            expect(deleteApiKeyMock).toHaveBeenCalledWith(201);
        });
        expect(screen.getByRole("dialog", { name: "Delete API key" })).toBeInTheDocument();
    });
});
