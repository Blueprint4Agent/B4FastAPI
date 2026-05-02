export type APIKeyExpiryOption = "7d" | "30d" | "90d" | "never";

const API_KEY_EXPIRY_DAYS: Record<Exclude<APIKeyExpiryOption, "never">, number> = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
};

function normalizeDateTimeInput(value: string): string {
    const trimmed = value.trim().replace(" ", "T");
    const match = trimmed.match(/^(.*?)(\.\d+)?(Z|[+\-]\d{2}:\d{2})?$/);
    if (!match) {
        return trimmed;
    }

    const base = match[1] ?? trimmed;
    const fraction = match[2] ?? "";
    const timezone = match[3] ?? "Z";
    const milliseconds = fraction ? `.${fraction.slice(1, 4).padEnd(3, "0")}` : "";
    return `${base}${milliseconds}${timezone}`;
}

export function resolveAPIKeyExpiresAt(
    option: APIKeyExpiryOption,
    now: Date = new Date(),
): string | null {
    if (option === "never") {
        return null;
    }
    const expiresAt = new Date(now);
    expiresAt.setUTCDate(expiresAt.getUTCDate() + API_KEY_EXPIRY_DAYS[option]);
    return expiresAt.toISOString();
}

export function formatDateYYYYMMDD(value: string | null | undefined, fallback = "-"): string {
    if (!value) {
        return fallback;
    }

    const date = new Date(normalizeDateTimeInput(value));
    if (Number.isNaN(date.getTime())) {
        return fallback;
    }

    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, "0");
    const day = String(date.getUTCDate()).padStart(2, "0");
    return `${year}/${month}/${day}`;
}

export function isDateTimeExpired(value: string | null | undefined, now: Date = new Date()): boolean {
    if (!value) {
        return false;
    }

    const parsed = new Date(normalizeDateTimeInput(value));
    if (Number.isNaN(parsed.getTime())) {
        return false;
    }

    return parsed.getTime() <= now.getTime();
}
