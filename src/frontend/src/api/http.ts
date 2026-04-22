import createClient from "openapi-fetch";

import { getAccessToken } from "../store/session";
import { getApiBase } from "../utils/apiBase";
import type { paths } from "./generated/openapi";

export type APIError = {
    detail?: {
        error?: string;
        message?: string;
        details?: Record<string, unknown>;
    };
};

export function getAuthHeader(): HeadersInit | undefined {
    const token = getAccessToken();
    if (!token) return undefined;
    return { Authorization: `Bearer ${token}` };
}

export const apiClient = createClient<paths>({
    baseUrl: getApiBase(),
    credentials: "include",
});
