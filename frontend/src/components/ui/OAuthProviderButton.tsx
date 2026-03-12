import { Button } from "./Button";

type OAuthProviderButtonProps = {
  provider: "google" | "github";
  label: string;
  startPath: string;
  disabled?: boolean;
};

const PROVIDER_BADGE: Record<OAuthProviderButtonProps["provider"], string> = {
  google: "G",
  github: "GH"
};

export function OAuthProviderButton({
  provider,
  label,
  startPath,
  disabled = false
}: OAuthProviderButtonProps) {
  const onClick = () => {
    window.location.assign(startPath);
  };

  return (
    <Button type="button" className="ui-button--oauth" disabled={disabled} onClick={onClick}>
      <span className="oauth-provider-button__content">
        <span className="oauth-provider-button__badge" aria-hidden="true">
          {PROVIDER_BADGE[provider]}
        </span>
        <span>{label}</span>
      </span>
    </Button>
  );
}
