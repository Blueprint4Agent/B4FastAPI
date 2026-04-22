import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
    children: ReactNode;
    loading?: boolean;
};

export function Button({
    children,
    className,
    type = "button",
    loading = false,
    disabled,
    ...props
}: ButtonProps) {
    const nextClassName = className ? `ui-button ${className}` : "ui-button";
    const isDisabled = Boolean(disabled || loading);

    return (
        <button type={type} className={nextClassName} disabled={isDisabled} {...props}>
            <span className="ui-button__content">
                {loading ? <span className="ui-button__spinner" aria-hidden="true" /> : null}
                <span>{children}</span>
            </span>
        </button>
    );
}
