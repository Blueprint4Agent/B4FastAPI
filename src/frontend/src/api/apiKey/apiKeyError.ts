import type { TFunction } from "i18next";

import type { components } from "../generated/openapi";

type APIKeyErrorDetailSchema = components["schemas"]["APIKeyErrorDetail"];

export type APIKeyErrorCode = APIKeyErrorDetailSchema["error"];

const API_KEY_ERROR_CODES = [
    "API_KEY_INVALID",
    "API_KEY_USER_MISMATCH",
    "API_KEY_CREATE_FAILED",
    "API_KEY_NAME_ALREADY_EXISTS",
    "API_KEY_NOT_FOUND",
    "API_KEY_UPDATE_FAILED",
] as const satisfies readonly APIKeyErrorCode[];

const API_KEY_ERROR_CODE_SET = new Set<APIKeyErrorCode>(API_KEY_ERROR_CODES);

type ApiError = {
    detail?: APIKeyErrorDetailSchema | { error?: unknown; message?: unknown; details?: unknown };
};

const API_KEY_ERROR_CODE_TO_KEY: Record<APIKeyErrorCode, string> = {
    API_KEY_INVALID: "settings.developers.errors.apiKeyInvalid",
    API_KEY_USER_MISMATCH: "settings.developers.errors.userMismatch",
    API_KEY_CREATE_FAILED: "settings.developers.errors.createFailed",
    API_KEY_NAME_ALREADY_EXISTS: "settings.developers.errors.nameAlreadyExists",
    API_KEY_NOT_FOUND: "settings.developers.errors.notFound",
    API_KEY_UPDATE_FAILED: "settings.developers.errors.updateFailed",
};

export type APIKeyErrorDetail = Partial<Pick<APIKeyErrorDetailSchema, "error" | "message">> & {
    details?: Record<string, unknown> | null;
};

function isAPIKeyErrorCode(value: unknown): value is APIKeyErrorCode {
    return typeof value === "string" && API_KEY_ERROR_CODE_SET.has(value as APIKeyErrorCode);
}

export function extractAPIKeyErrorDetail(error: unknown): APIKeyErrorDetail | null {
    if (!error || typeof error !== "object") return null;
    const detail = (error as ApiError).detail;
    if (!detail || typeof detail !== "object") return null;

    const rawError = (detail as { error?: unknown }).error;
    const rawMessage = (detail as { message?: unknown }).message;
    const rawDetails = (detail as { details?: unknown }).details;

    return {
        error: isAPIKeyErrorCode(rawError) ? rawError : undefined,
        message: typeof rawMessage === "string" ? rawMessage : undefined,
        details:
            rawDetails && typeof rawDetails === "object"
                ? (rawDetails as APIKeyErrorDetail["details"])
                : undefined,
    };
}

export function resolveAPIKeyErrorMessage(
    t: TFunction,
    detail: APIKeyErrorDetail | null,
    fallbackKey: string,
): string {
    const code = detail?.error;
    if (code) {
        const i18nKey = API_KEY_ERROR_CODE_TO_KEY[code];
        if (i18nKey) {
            return t(i18nKey);
        }
    }

    return detail?.message || detail?.error || t(fallbackKey);
}
