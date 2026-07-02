import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConnectivityBanner } from "../../../components/layout/ConnectivityBanner";
import {
    ServerConnectivityProvider,
    useServerConnectivity,
} from "../../../hooks/connectivity/useServerConnectivity";

const getServerReadinessMock = vi.fn();
const normalizeSystemErrorMock = (error: unknown) => ({
    message: error instanceof Error ? error.message : "failed",
});

vi.mock("../../../hooks/api/system/useSystemApi", () => ({
    useSystemApi: () => ({
        getServerReadiness: getServerReadinessMock,
        normalizeSystemError: normalizeSystemErrorMock,
    }),
}));

function ConnectivityProbe() {
    const { status } = useServerConnectivity();
    return <p data-testid="connectivity-status">{status}</p>;
}

describe("ServerConnectivityProvider", () => {
    beforeEach(() => {
        getServerReadinessMock.mockReset();
        Object.defineProperty(window.navigator, "onLine", {
            configurable: true,
            value: true,
        });
    });

    afterEach(() => {
        Reflect.deleteProperty(window, "__TAURI_INTERNALS__");
    });

    it("keeps browser runtime online without starting desktop health probes", () => {
        // Given: the frontend runs in a normal browser window.
        getServerReadinessMock.mockResolvedValue({ status: "ok", checks: {} });

        // When: the connectivity provider initializes.
        render(
            <ServerConnectivityProvider>
                <ConnectivityProbe />
                <ConnectivityBanner />
            </ServerConnectivityProvider>,
        );

        // Then: browser behavior remains online and no readiness request is made.
        expect(screen.getByTestId("connectivity-status")).toHaveTextContent("online");
        expect(screen.queryByRole("status")).not.toBeInTheDocument();
        expect(getServerReadinessMock).not.toHaveBeenCalled();
    });

    it("reports a desktop outage and returns online after a manual retry", async () => {
        // Given: Tauri starts while the server is unavailable, then the server recovers.
        Object.defineProperty(window, "__TAURI_INTERNALS__", {
            configurable: true,
            value: {},
        });
        getServerReadinessMock
            .mockRejectedValueOnce(new Error("server unavailable"))
            .mockResolvedValue({ status: "ok", checks: { database: "ok", redis: "ok" } });

        render(
            <ServerConnectivityProvider>
                <ConnectivityProbe />
                <ConnectivityBanner />
            </ServerConnectivityProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("connectivity-status")).toHaveTextContent("offline");
        });
        expect(screen.getByRole("status")).toBeInTheDocument();

        // When: the user requests an immediate connection retry.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: /retry|다시 시도/i }));

        // Then: successful readiness restores online state and removes the outage banner.
        await waitFor(() => {
            expect(screen.getByTestId("connectivity-status")).toHaveTextContent("online");
        });
        expect(screen.queryByRole("status")).not.toBeInTheDocument();
        expect(getServerReadinessMock).toHaveBeenCalledTimes(2);
    });
});
