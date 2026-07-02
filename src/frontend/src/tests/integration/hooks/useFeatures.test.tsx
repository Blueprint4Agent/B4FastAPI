import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAppConfig } from "../../../hooks/useFeatures";

const getConfigMock = vi.fn();

vi.mock("../../../hooks/api/config/useConfigApi", () => ({
    useConfigApi: () => ({ getConfig: getConfigMock }),
}));

vi.mock("../../../hooks/connectivity/useServerConnectivity", () => ({
    useServerConnectivity: () => ({ isDesktop: true, status: "offline" }),
}));

function AppConfigProbe() {
    const { data, loading, error, reload } = useAppConfig();

    return (
        <section>
            <p data-testid="loading">{String(loading)}</p>
            <p data-testid="error">{String(Boolean(error))}</p>
            <p data-testid="login-enabled">{String(data?.login_enabled ?? "unknown")}</p>
            <button type="button" onClick={() => void reload().catch(() => undefined)}>
                reload
            </button>
        </section>
    );
}

describe("useAppConfig", () => {
    beforeEach(() => {
        getConfigMock.mockReset();
    });

    it("keeps missing configuration distinct from explicitly disabled login", async () => {
        // Given: initial configuration loading fails while the server is offline.
        getConfigMock
            .mockRejectedValueOnce(new Error("server unavailable"))
            .mockResolvedValueOnce({ login_enabled: true });

        render(<AppConfigProbe />);

        // Then: missing data is exposed as an error, not login_enabled=false.
        await waitFor(() => {
            expect(screen.getByTestId("loading")).toHaveTextContent("false");
        });
        expect(screen.getByTestId("error")).toHaveTextContent("true");
        expect(screen.getByTestId("login-enabled")).toHaveTextContent("unknown");

        // When: the server recovers and configuration is requested again.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "reload" }));

        // Then: the successful server value replaces the unavailable state.
        await waitFor(() => {
            expect(screen.getByTestId("login-enabled")).toHaveTextContent("true");
        });
        expect(screen.getByTestId("error")).toHaveTextContent("false");
        expect(getConfigMock).toHaveBeenCalledTimes(2);
    });
});
