export const FULL_SYSTEM_SCENARIO = {
    principal: {
        id: 1,
        email: "seeded-primary@example.com",
        name: "Seeded Primary User",
        profile_image_url: null,
        oauth_providers: ["google"],
        is_verified: true,
        created_at: "2026-04-26T00:00:00Z",
    },
    auth: {
        validPassword: "SeededPass1!",
        invalidPassword: "WrongPass1!",
        malformedEmail: "invalid-email-format",
    },
    apiKey: {
        primaryName: "scenario-primary-key",
        secondaryName: "scenario-backup-key",
        secretPrefix: "sk_live_",
    },
} as const;
