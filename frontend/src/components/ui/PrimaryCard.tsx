import type { ReactNode } from "react";

type PrimaryCardProps = {
    children: ReactNode;
    className?: string;
};

export function PrimaryCard({ children, className }: PrimaryCardProps) {
    const nextClassName = className ? `primary-card ${className}` : "primary-card";

    return <section className={nextClassName}>{children}</section>;
}
