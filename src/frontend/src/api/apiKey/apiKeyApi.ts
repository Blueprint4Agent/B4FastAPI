import type { components } from "../generated/openapi";
import { apiClient, getAuthHeader } from "../http";

export type APIKeyRecord = components["schemas"]["APIKeyResponse"];
export type APIKeyListPayload = components["schemas"]["APIKeysResponse"];
export type APIKeyCreatePayload = components["schemas"]["APIKeyCreateResponse"];

export async function listApiKeys(): Promise<APIKeyListPayload> {
    const { data, error } = await apiClient.GET("/api/v1/api-keys", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function createApiKey(
    name: string,
    expiresAt: string | null = null,
): Promise<APIKeyCreatePayload> {
    const requestBody: components["schemas"]["APIKeyCreateForm"] = { name };
    if (expiresAt) {
        requestBody.expires_at = expiresAt;
    }

    const { data, error } = await apiClient.POST("/api/v1/api-keys", {
        headers: getAuthHeader(),
        body: requestBody,
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function deleteApiKey(apiKeyId: number): Promise<APIKeyRecord> {
    const { data, error } = await apiClient.DELETE("/api/v1/api-keys/{api_key_id}", {
        headers: getAuthHeader(),
        params: {
            path: {
                api_key_id: apiKeyId,
            },
        },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function updateApiKeyStatus(
    apiKeyId: number,
    enabled: boolean,
): Promise<APIKeyRecord> {
    const { data, error } = await apiClient.PATCH("/api/v1/api-keys/{api_key_id}/status", {
        headers: getAuthHeader(),
        params: {
            path: {
                api_key_id: apiKeyId,
            },
        },
        body: { enabled },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}
