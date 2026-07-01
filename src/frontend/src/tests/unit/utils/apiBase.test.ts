import { describe, expect, it } from "vitest";

import { alignLoopbackApiBase } from "../../../utils/apiBase";

describe("alignLoopbackApiBase", () => {
    it("aligns localhost API requests with a 127.0.0.1 frontend", () => {
        // Given: local frontend and API use different loopback hostnames.
        // When: the configured API base is normalized.
        const apiBase = alignLoopbackApiBase("http://localhost:8000", "127.0.0.1");

        // Then: both origins use the same cookie site while preserving the API port.
        expect(apiBase).toBe("http://127.0.0.1:8000/");
    });

    it("does not rewrite a non-loopback API hostname", () => {
        // Given: a deployed API hostname is configured.
        // When: the API base is normalized from a local frontend.
        const apiBase = alignLoopbackApiBase("https://api.example.com", "localhost");

        // Then: the explicit deployment hostname remains unchanged.
        expect(apiBase).toBe("https://api.example.com");
    });
});
