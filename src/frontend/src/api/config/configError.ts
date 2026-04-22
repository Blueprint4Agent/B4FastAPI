import type { TFunction } from "i18next";

type ConfigError = {
    detail?: {
        message?: string;
    };
};

export function extractConfigErrorMessage(error: unknown): string | null {
    if (!error || typeof error !== "object") return null;
    const detail = (error as ConfigError).detail;
    if (!detail || typeof detail !== "object") return null;

    const message = (detail as { message?: unknown }).message;
    return typeof message === "string" ? message : null;
}

export function resolveConfigErrorMessage(
    t: TFunction,
    error: unknown,
    fallbackKey: string,
): string {
    return extractConfigErrorMessage(error) || t(fallbackKey);
}
