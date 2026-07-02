import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { getServerReadiness } from "../../../api/system/systemApi";
import { server } from "../../mocks/server";

describe("systemApi.getServerReadiness", () => {
    it("returns readiness details when the server and dependencies are ready", async () => {
        // Given: the readiness endpoint reports healthy dependencies.
        server.use(
            http.get(/.*\/health\/ready$/, () =>
                HttpResponse.json({
                    status: "ok",
                    checks: { database: "ok", redis: "ok" },
                }),
            ),
        );

        // When: desktop connectivity checks the server.
        const readiness = await getServerReadiness();

        // Then: the typed readiness response is returned.
        expect(readiness.status).toBe("ok");
        expect(readiness.checks).toEqual({ database: "ok", redis: "ok" });
    });

    it("rejects a degraded server response", async () => {
        // Given: the backend process responds but a required dependency is unavailable.
        server.use(
            http.get(/.*\/health\/ready$/, () =>
                HttpResponse.json(
                    {
                        status: "degraded",
                        checks: { database: "failed", redis: "ok" },
                    },
                    { status: 503 },
                ),
            ),
        );

        // When/Then: degraded readiness is treated as an unavailable server.
        await expect(getServerReadiness()).rejects.toThrow("readiness check failed (503)");
    });
});
