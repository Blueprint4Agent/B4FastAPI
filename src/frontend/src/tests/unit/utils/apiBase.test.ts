import { describe, expect, it } from "vitest";

import { alignLoopbackApiBase, resolveDefaultApiBase } from "../../../utils/apiBase";

const browserLocation = {
    hostname: "127.0.0.1",
    origin: "http://127.0.0.1:5173",
    port: "5173",
    protocol: "http:",
};

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

    it("keeps the browser development API on the current loopback host", () => {
        // Given: the browser frontend is served from the Vite development port.
        // When: its default API base is resolved.
        const apiBase = resolveDefaultApiBase(browserLocation, false);

        // Then: the existing browser target continues using the same host on port 8000.
        expect(apiBase).toBe("http://127.0.0.1:8000");
    });

    it("uses the local backend for the optional Tauri development shell", () => {
        // Given: the frontend is running inside Tauri's custom protocol.
        // When: its default API base is resolved.
        const apiBase = resolveDefaultApiBase(undefined, true);

        // Then: desktop development targets the local FastAPI server.
        expect(apiBase).toBe("http://localhost:8000");
    });
});
