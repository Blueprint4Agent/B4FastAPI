import type { ReactNode } from "react";

type StatusCardProps = {
    title: string;
    message: string;
    tone: "error" | "warning" | "info";
    children?: ReactNode;
};

export function StatusCard({ title, message, tone, children }: StatusCardProps) {
    return (
        <div className={`status-card status-card--${tone}`} role="alert" aria-live="polite">
            <div className="status-card__title">{title}</div>
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
