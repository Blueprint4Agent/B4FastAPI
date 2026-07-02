import { describe, expect, it } from "vitest";

import { getReconnectDelayMs } from "../../../hooks/connectivity/useServerConnectivity";

describe("server connectivity backoff", () => {
    it("uses exponential delays capped at thirty seconds", () => {
        // Given: deterministic midpoint jitter.
        const midpointJitter = 0.5;

        // When/Then: delay doubles until the configured maximum is reached.
        expect(getReconnectDelayMs(1, midpointJitter)).toBe(1_000);
        expect(getReconnectDelayMs(2, midpointJitter)).toBe(2_000);
        expect(getReconnectDelayMs(5, midpointJitter)).toBe(16_000);
        expect(getReconnectDelayMs(6, midpointJitter)).toBe(30_000);
        expect(getReconnectDelayMs(20, midpointJitter)).toBe(30_000);
    });

    it("adds bounded jitter to avoid synchronized reconnect attempts", () => {
        // Given/When: the minimum and maximum jitter values are applied.
        const minimumDelay = getReconnectDelayMs(2, 0);
        const maximumDelay = getReconnectDelayMs(2, 1);

        // Then: jitter stays within plus or minus twenty percent.
        expect(minimumDelay).toBe(1_600);
        expect(maximumDelay).toBe(2_400);
    });
});
