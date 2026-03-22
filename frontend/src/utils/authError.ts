import type { TFunction } from "i18next";

export type ApiErrorDetail = {
    error?: string;
    message?: string;
    details?: {
        remaining_attempts?: number;
        remaining_seconds?: number;
    };
};

type ApiError = {
    detail?: ApiErrorDetail;
};

const AUTH_ERROR_CODE_TO_KEY: Record<string, string> = {
    EMAIL_ALREADY_EXISTS: "auth.errors.emailAlreadyExists",
    EMAIL_DISABLED: "auth.errors.emailDisabled",
    INVALID_TOKEN: "auth.errors.invalidToken",
    USER_NOT_FOUND: "auth.errors.userNotFound",
    OAUTH_PROVIDER_NOT_ENABLED: "auth.errors.oauthProviderNotEnabled",
    OAUTH_PROVIDER_CONFIG_INVALID: "auth.errors.oauthProviderConfigInvalid",
    OAUTH_IDENTITY_CONFLICT: "auth.errors.oauthIdentityConflict",
    OAUTH_SIGNUP_FAILED: "auth.errors.oauthSignupFailed",
    OAUTH_PROVIDER_REQUEST_FAILED: "auth.errors.oauthProviderRequestFailed",
};

export function extractApiDetail(error: unknown): ApiErrorDetail | null {
    if (!error || typeof error !== "object") return null;
    const detail = (error as ApiError).detail;
    if (!detail || typeof detail !== "object") return null;
    return detail;
}

export function resolveAuthErrorMessage(
    t: TFunction,
    detail: ApiErrorDetail | null,
    fallbackKey: string,
): string {
    const code = detail?.error;
    if (code) {
        const i18nKey = AUTH_ERROR_CODE_TO_KEY[code];
        if (i18nKey) {
            return t(i18nKey);
        }
    }
    return detail?.message || detail?.error || t(fallbackKey);
}
