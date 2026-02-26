import type { ReactNode } from "react";

type KeyValueCardProps = {
  label: string;
  value: ReactNode;
};

export function KeyValueCard({ label, value }: KeyValueCardProps) {
  return (
    <div className="key-value-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
