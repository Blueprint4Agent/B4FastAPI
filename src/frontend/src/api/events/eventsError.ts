export type EventsStreamErrorDetail = {
    status?: number;
    message?: string;
};

export function normalizeEventsStreamError(error: unknown): EventsStreamErrorDetail {
    if (error instanceof Error) {
        return { message: error.message };
    }
    if (typeof error === "string") {
        return { message: error };
    }
    if (!error || typeof error !== "object") {
        return {};
    }

    const status = (error as { status?: unknown }).status;
    const message = (error as { message?: unknown }).message;
    return {
        status: typeof status === "number" ? status : undefined,
        message: typeof message === "string" ? message : undefined,
    };
}
