import type { ReactNode } from "react";

type StatusCardProps = {
    title?: string;
    message: string;
    tone: "error" | "warning" | "info";
    compact?: boolean;
    children?: ReactNode;
};

export function StatusCard({ title, message, tone, compact = false, children }: StatusCardProps) {
    const className = compact
        ? `status-card status-card--${tone} status-card--compact`
        : `status-card status-card--${tone}`;
    return (
        <div className={className} role="alert" aria-live="polite">
            {title ? <div className="status-card__title">{title}</div> : null}
            <div className="status-card__message">{message}</div>
            {children}
        </div>
    );
}

export function ErrorCard({ title, message, children }: Omit<StatusCardProps, "tone">) {
    return (
        <StatusCard title={title} message={message} tone="error">
            {children}
        </StatusCard>
    );
}

export function WarningCard({ title, message, children }: Omit<StatusCardProps, "tone">) {
    return (
        <StatusCard title={title} message={message} tone="warning">
            {children}
        </StatusCard>
    );
}

export function InfoCard({ title, message, children }: Omit<StatusCardProps, "tone">) {
    return (
        <StatusCard title={title} message={message} tone="info">
            {children}
        </StatusCard>
    );
}
