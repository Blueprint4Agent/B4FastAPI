import { getAccessToken } from "../../store/session";
import { getApiBase } from "../../utils/apiBase";

export type RealtimeEventType =
    | "connected"
    | "ping"
    | "api_key.created"
    | "api_key.status_updated"
    | "api_key.deleted";

export type RealtimeEvent = {
    id: string;
    type: RealtimeEventType | string;
    version: string;
    ts: string;
    payload: Record<string, unknown>;
};

type RawSSEMessage = {
    id?: string;
    event?: string;
    data?: string;
    retry?: number;
};

type StreamOptions = {
    signal: AbortSignal;
    onEvent: (event: RealtimeEvent) => void;
    onError?: (error: unknown) => void;
};

const SSE_STREAM_PATH = "/api/v1/events/stream";

function parseSSEMessageBlock(block: string): RawSSEMessage | null {
    if (!block.trim()) {
        return null;
    }

    const message: RawSSEMessage = {};
    const dataLines: string[] = [];

    const lines = block.split("\n");
    for (const rawLine of lines) {
        if (!rawLine || rawLine.startsWith(":")) {
            continue;
        }

        const separatorIndex = rawLine.indexOf(":");
        const field = separatorIndex < 0 ? rawLine : rawLine.slice(0, separatorIndex);
        const value = separatorIndex < 0 ? "" : rawLine.slice(separatorIndex + 1).trimStart();

        if (field === "event") {
            message.event = value;
            continue;
        }
        if (field === "id") {
            message.id = value;
            continue;
        }
        if (field === "retry") {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isNaN(parsed)) {
                message.retry = parsed;
            }
            continue;
        }
        if (field === "data") {
            dataLines.push(value);
        }
    }

    if (dataLines.length > 0) {
        message.data = dataLines.join("\n");
    }

    if (!message.data && !message.event && !message.id && typeof message.retry === "undefined") {
        return null;
    }
    return message;
}

function parseRealtimeEvent(rawMessage: RawSSEMessage): RealtimeEvent | null {
    if (!rawMessage.data) {
        return null;
    }

    const parsed = JSON.parse(rawMessage.data) as Partial<RealtimeEvent>;
    if (!parsed || typeof parsed !== "object") {
        return null;
    }
    if (typeof parsed.type !== "string") {
        return null;
    }

    return {
        id: typeof parsed.id === "string" ? parsed.id : "",
        type: parsed.type,
        version: typeof parsed.version === "string" ? parsed.version : "v1",
        ts: typeof parsed.ts === "string" ? parsed.ts : new Date().toISOString(),
        payload:
            parsed.payload && typeof parsed.payload === "object"
                ? (parsed.payload as Record<string, unknown>)
                : {},
    };
}

export async function streamRealtimeEvents({
    signal,
    onEvent,
    onError,
}: StreamOptions): Promise<void> {
    const accessToken = getAccessToken();
    if (!accessToken) {
        throw new Error("Access token is missing.");
    }

    const response = await fetch(`${getApiBase()}${SSE_STREAM_PATH}`, {
        method: "GET",
        headers: {
            Accept: "text/event-stream",
            Authorization: `Bearer ${accessToken}`,
            "Cache-Control": "no-cache",
        },
        credentials: "include",
        signal,
    });

    if (!response.ok) {
        const bodyText = await response.text().catch(() => "");
        const error = new Error(
            `SSE stream request failed (${response.status}): ${bodyText || response.statusText}`,
        );
        onError?.(error);
        throw error;
    }

    if (!response.body) {
        const error = new Error("SSE response body is unavailable.");
        onError?.(error);
        throw error;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
        while (!signal.aborted) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            if (!value) {
                continue;
            }

            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, "\n");

            let delimiterIndex = buffer.indexOf("\n\n");
            while (delimiterIndex >= 0) {
                const rawBlock = buffer.slice(0, delimiterIndex);
                buffer = buffer.slice(delimiterIndex + 2);

                const message = parseSSEMessageBlock(rawBlock);
                if (message) {
                    try {
                        const event = parseRealtimeEvent(message);
                        if (event) {
                            onEvent(event);
                        }
                    } catch (eventParseError) {
                        onError?.(eventParseError);
                    }
                }

                delimiterIndex = buffer.indexOf("\n\n");
            }
        }
    } finally {
        reader.releaseLock();
    }
}
