# Optional WebSocket provider

`src/frontend/src/hooks/realtime/websocket/WebSocketProvider.tsx` is an opt-in transport template. It is not mounted in App and opens no connection by default. Notifications and support still use the existing SSE endpoint. This change does not add a server WebSocket route, authentication protocol, subscription protocol or message schema.

Wrap only the feature that needs a socket. Supply `enabled`, an account/session-specific `sessionKey`, a stable `useCallback` connection factory and an optional `onMessage`. `useWebSocket()` exposes status, `send(string): boolean` and `reconnect()`. A failed send returns false and is never silently queued/replayed.

```tsx
const connection = useCallback(async (signal: AbortSignal) => {
    // Implement the domain API to obtain an authorized connection descriptor.
    // The backend must authenticate and authorize both the connection and messages.
    return getAuthorizedSocketConnection(signal);
}, []);

<WebSocketProvider
    enabled={featureEnabled && Boolean(user)}
    sessionKey={user?.id ?? null}
    getConnection={connection}
    onMessage={handleDomainMessage}
>
    <Feature />
</WebSocketProvider>
```

The descriptor is `{ url, protocols? }`; only ws/wss URLs without username/password are accepted. Use wss in deployment. The native browser constructor cannot set arbitrary Authorization headers: decide cookie/Origin validation or a short-lived socket ticket in the future backend implementation. Never put a long-lived bearer token in a URL. The provider does not invent or persist authentication credentials.

The owner controls parsing, validation, event subscriptions and HTTP reconciliation; incoming payloads are delivered as unknown and are not retained in shared React state. Updating the callback does not reconnect. Changing session, disabling, going offline or unmounting aborts pending factories, closes sockets, clears timers and discards stale callbacks. Desktop connectivity recovery and browser online recovery reconnect. Network failures retry at 1/2/4/8/16 seconds, at most five retries per connection generation; explicit `reconnect()` starts a new generation. Normal close (1000) and policy failure (1008) stop automatic retries. Transport buffering above 64 KiB rejects new sends; there is no application-level message queue.
