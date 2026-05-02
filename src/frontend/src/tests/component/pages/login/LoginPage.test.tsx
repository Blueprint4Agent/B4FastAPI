import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "../../../../pages/login/LoginPage";
import { FULL_SYSTEM_SCENARIO } from "../../../fixtures/fullSystemScenarioData";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const navigateMock = vi.fn();
const loginMock = vi.fn();
const resendVerificationEmailMock = vi.fn();
const extractApiDetailMock = vi.fn();
const resolveAuthErrorMessageMock = vi.fn(() => "Login failed.");

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
    return {
        ...actual,
        useNavigate: () => navigateMock,
    };
});

vi.mock("../../../../hooks/useAuth", () => ({
    useAuthContext: () => ({
        user: null,
        loading: false,
        login: loginMock,
        signup: vi.fn(),
        updateProfile: vi.fn(),
        logout: vi.fn(),
        refreshSession: vi.fn(),
    }),
}));

vi.mock("../../../../hooks/useFeatures", () => ({
    useAppConfig: () => ({
        data: {
            login_enabled: true,
            email_enabled: true,
            oauth_enabled: false,
        },
        loading: false,
    }),
}));

vi.mock("../../../../hooks/api/auth/useAuthApi", () => ({
    useAuthApi: () => ({
        getOAuthProviders: vi.fn().mockResolvedValue({ providers: [] }),
        resendVerificationEmail: resendVerificationEmailMock,
        extractApiDetail: extractApiDetailMock,
        resolveAuthErrorMessage: resolveAuthErrorMessageMock,
    }),
}));

describe("LoginPage", () => {
    beforeEach(() => {
        navigateMock.mockReset();
        loginMock.mockReset();
        resendVerificationEmailMock.mockReset();
        extractApiDetailMock.mockReset();
        resolveAuthErrorMessageMock.mockReset();
        resolveAuthErrorMessageMock.mockReturnValue("Login failed.");

        extractApiDetailMock.mockImplementation((error: unknown) => {
            if (!error || typeof error !== "object") {
                return null;
            }
            const detail = (error as { detail?: unknown }).detail;
            if (!detail || typeof detail !== "object") {
                return null;
            }
            return detail as {
                error?: string;
                message?: string;
                details?: Record<string, unknown>;
            };
        });
    });

    it("shows validation error when email format is invalid", async () => {
        // Given: login page is rendered.
        renderWithRouter(<LoginPage />, "/login");
        const user = userEvent.setup();

        // When: malformed email and valid password are submitted.
        await user.type(screen.getByLabelText("Email"), FULL_SYSTEM_SCENARIO.auth.malformedEmail);
        await user.type(screen.getByLabelText("Password"), FULL_SYSTEM_SCENARIO.auth.validPassword);
        await user.click(screen.getByRole("button", { name: "Sign in" }));

        // Then: inline email validation message is shown.
        expect(screen.getByText("Please enter a valid email address.")).toBeInTheDocument();
        expect(loginMock).not.toHaveBeenCalled();
    });

    it("navigates to show-case after successful login", async () => {
        // Given: successful login response from auth context.
        loginMock.mockResolvedValue(undefined);
        renderWithRouter(<LoginPage />, "/login");
        const user = userEvent.setup();

        // When: valid credentials are submitted.
        await user.type(screen.getByLabelText("Email"), FULL_SYSTEM_SCENARIO.principal.email);
        await user.type(screen.getByLabelText("Password"), FULL_SYSTEM_SCENARIO.auth.validPassword);
        await user.click(screen.getByRole("button", { name: "Sign in" }));

        // Then: auth login is called and route navigation is triggered.
        expect(loginMock).toHaveBeenCalledWith({
            email: FULL_SYSTEM_SCENARIO.principal.email,
            password: FULL_SYSTEM_SCENARIO.auth.validPassword,
            remember_me: false,
        });
        expect(navigateMock).toHaveBeenCalledWith("/show-case", { replace: true });
    });

    it("shows remaining attempts message when backend returns INVALID_CREDENTIALS", async () => {
        // Given: backend-style invalid-credentials detail with remaining attempts.
        loginMock.mockRejectedValue({
            detail: {
                error: "INVALID_CREDENTIALS",
                message: "Incorrect email or password.",
                details: { remaining_attempts: 3 },
            },
        });
        renderWithRouter(<LoginPage />, "/login");
        const user = userEvent.setup();

        // When: login is attempted with wrong password.
        await user.type(screen.getByLabelText("Email"), FULL_SYSTEM_SCENARIO.principal.email);
        await user.type(
            screen.getByLabelText("Password"),
            FULL_SYSTEM_SCENARIO.auth.invalidPassword,
        );
        await user.click(screen.getByRole("button", { name: "Sign in" }));

        // Then: remaining-attempts message branch is rendered.
        expect(
            screen.getByText("Incorrect credentials. 3 attempt(s) remaining."),
        ).toBeInTheDocument();
    });

    it("shows resend verification action on EMAIL_NOT_VERIFIED and handles resend", async () => {
        // Given: backend-style email-not-verified response.
        loginMock.mockRejectedValue({
            detail: {
                error: "EMAIL_NOT_VERIFIED",
                message: "Email verification is required.",
            },
        });
        resendVerificationEmailMock.mockResolvedValue({
            message: "Verification email has been sent.",
        });
        renderWithRouter(<LoginPage />, "/login");
        const user = userEvent.setup();

        // When: login is attempted and resend action is clicked.
        await user.type(screen.getByLabelText("Email"), FULL_SYSTEM_SCENARIO.principal.email);
        await user.type(screen.getByLabelText("Password"), FULL_SYSTEM_SCENARIO.auth.validPassword);
        await user.click(screen.getByRole("button", { name: "Sign in" }));
        await user.click(screen.getByRole("button", { name: "Resend verification email" }));

        // Then: resend endpoint is called and success message is displayed.
        expect(resendVerificationEmailMock).toHaveBeenCalledWith(
            FULL_SYSTEM_SCENARIO.principal.email,
        );
        expect(screen.getByText("Verification email has been sent.")).toBeInTheDocument();
    });
});
