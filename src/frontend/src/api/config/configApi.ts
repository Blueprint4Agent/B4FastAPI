import type { paths } from "../generated/openapi";
import { apiClient } from "../http";

export type AppConfig = paths["/config"]["get"]["responses"][200]["content"]["application/json"];

export async function getConfig(): Promise<AppConfig> {
    const { data, error } = await apiClient.GET("/config");
    if (error || !data) {
        throw error ?? new Error("Failed to load config.");
    }
    return data;
}
