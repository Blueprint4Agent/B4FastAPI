import { http, HttpResponse } from "msw";

export const handlers = [
    http.get(/.*\/config$/, () =>
        HttpResponse.json({
            api_base_path: "/api/v1",
            login_enabled: true,
            frontend_base_path: "",
            email_enabled: false,
            oauth_enabled: false,
            oauth_providers: [],
            bootstrap_user: null,
            bootstrap_access_token: null,
        }),
    ),
    http.get(/.*\/api\/v1\/auth\/me$/, () =>
        HttpResponse.json(
            {
                detail: {
                    error: "INVALID_TOKEN",
                    message: "Invalid token",
                },
            },
            { status: 401 },
        ),
    ),
    http.post(/.*\/api\/v1\/auth\/refresh$/, () =>
        HttpResponse.json(
            {
                detail: {
                    error: "INVALID_TOKEN",
                    message: "Invalid token",
                },
            },
            { status: 401 },
        ),
    ),
];
