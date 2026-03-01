import { apiClient, getAuthHeader } from "./http";
import type { components } from "./generated/openapi";

type SignupInput = components["schemas"]["SignupForm"];
type LoginInput = components["schemas"]["LoginForm"];
export type User = components["schemas"]["UserResponse"];
export type LoginPayload = components["schemas"]["LoginResponse"];
export type RefreshPayload = components["schemas"]["RefreshResponse"];

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

export async function me(): Promise<User> {
  const { data, error } = await apiClient.GET("/api/v1/auth/me", {
    headers: getAuthHeader()
  });
  if (error || !data) {
    throw error;
  }
  return data;
}

export async function refresh(): Promise<RefreshPayload> {
  const { data, error } = await apiClient.POST("/api/v1/auth/refresh", {
    body: {}
  });
  if (error || !data) {
    throw error;
  }
  return data;
}

export async function logout() {
  const { data, error } = await apiClient.POST("/api/v1/auth/logout", {
    headers: getAuthHeader()
  });
  if (error || !data) {
    throw error;
  }
  return data;
}
