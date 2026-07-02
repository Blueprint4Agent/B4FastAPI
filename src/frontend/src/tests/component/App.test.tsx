import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";

const reloadConfigMock = vi.fn();
const useAppConfigMock = vi.fn();

vi.mock("../../hooks/useFeatures", () => ({
    useAppConfig: () => useAppConfigMock(),
}));

vi.mock("../../hooks/useTheme", () => ({
    useTheme: () => ({ themeMode: "system", setThemeMode: vi.fn() }),
}));

describe("App configuration guard", () => {
    beforeEach(() => {
        reloadConfigMock.mockReset();
        reloadConfigMock.mockRejectedValue(new Error("server unavailable"));
        useAppConfigMock.mockReturnValue({
            data: null,
            loading: false,
            error: new Error("config unavailable"),
            reload: reloadConfigMock,
        });
    });

    it("keeps protected routes locked when server configuration is unavailable", async () => {
        // Given: desktop startup cannot load /config and the requested URL is protected.
        render(
            <MemoryRouter initialEntries={["/show-case"]}>
                <App />
            </MemoryRouter>,
        );

        // Then: the app fails closed instead of treating login as disabled or showing a fake user.
        expect(screen.getByRole("heading", { name: "Server unavailable" })).toBeInTheDocument();
        expect(screen.getByText(/protected pages remain locked/i)).toBeInTheDocument();
        expect(screen.queryByText("User")).not.toBeInTheDocument();

        // When: the user requests another connection attempt.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Retry connection" }));

        // Then: the application configuration is requested again.
        expect(reloadConfigMock).toHaveBeenCalledTimes(1);
    });
});
