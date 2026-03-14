import type { ReactNode } from "react";

type OAuthOptionsCardProps = {
  title: string;
  children: ReactNode;
};

export function OAuthOptionsCard({ title, children }: OAuthOptionsCardProps) {
  return (
    <section className="oauth-options-card">
      <p className="oauth-options-card__title">{title}</p>
      <div className="oauth-options-card__body">{children}</div>
    </section>
  );
}
