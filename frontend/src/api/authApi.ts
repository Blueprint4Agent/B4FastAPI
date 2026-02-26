import { request } from "./http";
import type { LoginPayload, RefreshPayload, User } from "./types";

export async function signup(input: { email: string; name: string; password: string }) {
  return request<User>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function login(input: { email: string; password: string; remember_me: boolean }) {
  return request<LoginPayload>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function me() {
  return request<User>("/api/v1/auth/me", { method: "GET", auth: true });
}

export async function refresh() {
  return request<RefreshPayload>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export async function logout() {
  return request<{ message: string }>("/api/v1/auth/logout", {
    method: "POST",
    auth: true
  });
}
