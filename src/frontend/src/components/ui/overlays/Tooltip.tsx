import type { FocusEvent, ReactNode } from "react";
import { useState } from "react";

type TooltipSide = "top" | "right" | "bottom" | "left";

type TooltipProps = {
    content: string;
    children: ReactNode;
    side?: TooltipSide;
    disabled?: boolean;
    className?: string;
};

export function Tooltip({
    content,
    children,
    side = "top",
    disabled = false,
    className,
}: TooltipProps) {
    const [open, setOpen] = useState(false);
    const nextClassName = className ? `ui-tooltip ${className}` : "ui-tooltip";
    const tooltipClassName = open
        ? `ui-tooltip__content ui-tooltip__content--${side} ui-tooltip__content--open`
        : `ui-tooltip__content ui-tooltip__content--${side}`;

    const handleBlurCapture = (event: FocusEvent<HTMLSpanElement>) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setOpen(false);
        }
    };

    return (
        <span
            className={nextClassName}
            onMouseEnter={() => {
                setOpen(true);
            }}
            onMouseLeave={() => {
                setOpen(false);
            }}
            onFocusCapture={() => {
                setOpen(true);
            }}
            onBlurCapture={handleBlurCapture}
            onClickCapture={() => {
                setOpen(false);
            }}
        >
            <span className="ui-tooltip__trigger">{children}</span>
            {disabled ? null : (
                <span role="tooltip" className={tooltipClassName} aria-hidden={!open}>
                    {content}
                </span>
            )}
        </span>
    );
}
