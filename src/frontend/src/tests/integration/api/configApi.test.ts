import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../../../api/http";
import { getConfig } from "../../../api/config/configApi";

afterEach(() => {
    vi.restoreAllMocks();
});

describe("configApi.getConfig", () => {
    it("returns app config payload on success", async () => {
        // Given: api client returns config payload.
        vi.spyOn(apiClient, "GET").mockResolvedValue({
            data: {
                api_base_path: "/api/v1",
                login_enabled: true,
                frontend_base_path: "",
                email_enabled: false,
                oauth_enabled: false,
                oauth_providers: [],
                bootstrap_user: null,
                bootstrap_access_token: null,
            },
            error: undefined,
            response: new Response(),
        } as never);

        // When: config API is requested.
        const payload = await getConfig();

        // Then: strongly typed config payload is returned.
        expect(payload.login_enabled).toBe(true);
        expect(payload.api_base_path).toBe("/api/v1");
    });

    it("throws when config endpoint fails", async () => {
        // Given: api client returns failure response.
        vi.spyOn(apiClient, "GET").mockResolvedValue({
            data: undefined,
            error: { detail: { error: "CONFIG_LOAD_FAILED", message: "Failed" } },
            response: new Response(),
        } as never);

        // When/Then: config call fails with error.
        await expect(getConfig()).rejects.toBeTruthy();
    });
});
