type ScenarioRole = "admin" | "user";

type FullSystemScenario = {
    principal: {
        id: number;
        email: string;
        name: string;
        role: ScenarioRole;
        profile_image_url: string | null;
        oauth_providers: string[];
        is_verified: boolean;
        created_at: string;
    };
    auth: {
        validPassword: string;
        invalidPassword: string;
        malformedEmail: string;
    };
    apiKey: {
        primaryName: string;
        secondaryName: string;
        secretPrefix: string;
    };
};

export const FULL_SYSTEM_SCENARIO: FullSystemScenario = {
    principal: {
        id: 1,
        email: "seeded-primary@example.com",
        name: "Seeded Primary User",
        role: "admin",
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
};
