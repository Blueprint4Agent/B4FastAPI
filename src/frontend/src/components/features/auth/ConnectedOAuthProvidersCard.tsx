import { Button } from "../../ui";

type ConnectedOAuthProvidersCardProps = {
    title: string;
    providers: string[];
    emptyText: string;
    getProviderLabel: (provider: string) => string;
};

const CONNECTED_OAUTH_PROVIDER_LOGOS: Record<string, { light: string; dark: string }> = {
    google: {
        light: "/icons/google-mark-light.svg",
        dark: "/icons/google-mark-dark.svg",
    },
    github: {
        light: "/icons/github-mark-light.svg",
        dark: "/icons/github-mark-dark.svg",
    },
};

export function ConnectedOAuthProvidersCard({
    title,
    providers,
    emptyText,
    getProviderLabel,
}: ConnectedOAuthProvidersCardProps) {
    return (
        <article className="settings-profile-field-card">
            <h2>{title}</h2>
            {providers.length > 0 ? (
                <div className="settings-oauth-provider-list">
                    {providers.map((provider) => (
                        <Button
                            key={provider}
                            className="settings-oauth-provider-button"
                            type="button"
                            disabled
                        >
                            <span className="settings-oauth-provider-button__content">
                                {CONNECTED_OAUTH_PROVIDER_LOGOS[provider] ? (
                                    <span
                                        className="oauth-provider-button__logo-wrap"
                                        aria-hidden="true"
                                    >
                                        <img
                                            src={CONNECTED_OAUTH_PROVIDER_LOGOS[provider].dark}
                                            alt=""
                                            className={`oauth-provider-button__logo oauth-provider-button__logo--dark oauth-provider-button__logo--${provider}`}
                                        />
                                        <img
                                            src={CONNECTED_OAUTH_PROVIDER_LOGOS[provider].light}
                                            alt=""
                                            className={`oauth-provider-button__logo oauth-provider-button__logo--light oauth-provider-button__logo--${provider}`}
                                        />
                                    </span>
                                ) : null}
                                <span className="settings-oauth-provider-button__label">
                                    {getProviderLabel(provider)}
                                </span>
                            </span>
                        </Button>
                    ))}
                </div>
            ) : (
                <p>{emptyText}</p>
            )}
        </article>
    );
}
