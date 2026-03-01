import createClient from "openapi-fetch";

import { getAccessToken } from "../store/session";
import type { paths } from "./generated/openapi";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type APIError = {
  detail?: {
    error?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

export function getApiBase(): string {
  return API_BASE.replace(/\/+$/, "");
}

export function getAuthHeader(): HeadersInit | undefined {
  const token = getAccessToken();
  if (!token) return undefined;
  return { Authorization: `Bearer ${token}` };
}

export const apiClient = createClient<paths>({
  baseUrl: getApiBase(),
  credentials: "include"
});
