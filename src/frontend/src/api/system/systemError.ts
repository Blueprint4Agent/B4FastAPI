export type SystemErrorDetail = {
    message: string;
};

export function normalizeSystemError(error: unknown): SystemErrorDetail {
    if (error instanceof Error && error.message) {
        return { message: error.message };
    }
    return { message: "Server connectivity check failed." };
}
