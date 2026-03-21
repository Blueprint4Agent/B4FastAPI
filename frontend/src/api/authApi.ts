import type { components } from "./generated/openapi";
import { apiClient, getAuthHeader } from "./http";

type SignupInput = components["schemas"]["SignupForm"];
type LoginInput = components["schemas"]["LoginForm"];
export type User = components["schemas"]["UserResponse"];
export type LoginPayload = components["schemas"]["LoginResponse"];
export type RefreshPayload = components["schemas"]["RefreshResponse"];
export type VerifyEmailPayload = components["schemas"]["VerifyEmailResponse"];
export type ResendVerificationPayload = components["schemas"]["ResendVerificationResponse"];
export type ForgotPasswordPayload = components["schemas"]["ForgotPasswordResponse"];
export type ResetPasswordPayload = components["schemas"]["ResetPasswordResponse"];
export type OAuthProvider = components["schemas"]["OAuthProvider"];
export type OAuthProvidersPayload = components["schemas"]["OAuthProvidersResponse"];

export async function signup(input: SignupInput): Promise<User> {
    const { data, error } = await apiClient.POST("/api/v1/auth/signup", { body: input });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function login(input: LoginInput): Promise<LoginPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/login", { body: input });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function getOAuthProviders(): Promise<OAuthProvidersPayload> {
    const { data, error } = await apiClient.GET("/api/v1/auth/oauth/providers");
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function me(): Promise<User> {
    const { data, error } = await apiClient.GET("/api/v1/auth/me", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function refresh(): Promise<RefreshPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/refresh", {
        body: {},
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function logout() {
    const { data, error } = await apiClient.POST("/api/v1/auth/logout", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function verifyEmail(token: string): Promise<VerifyEmailPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/verify-email", {
        body: { token },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function resendVerificationEmail(email: string): Promise<ResendVerificationPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/resend-verification", {
        body: { email },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function requestPasswordReset(email: string): Promise<ForgotPasswordPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/forgot-password", {
        body: { email },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function resetPassword(
    token: string,
    password: string,
): Promise<ResetPasswordPayload> {
    const { data, error } = await apiClient.POST("/api/v1/auth/reset-password", {
        body: { token, password },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}
