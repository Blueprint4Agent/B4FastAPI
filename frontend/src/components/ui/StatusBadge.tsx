import type { ReactNode } from "react";

type StatusBadgeTone = "active" | "inactive" | "info" | "danger";

type StatusBadgeProps = {
    children: ReactNode;
    tone: StatusBadgeTone;
};

export function StatusBadge({ children, tone }: StatusBadgeProps) {
    return (
        <span className={`ui-status-badge ui-status-badge--${tone}`} role="status">
            {children}
        </span>
    );
}
