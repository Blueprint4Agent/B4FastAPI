import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Button } from "./Button";

type ModalButtonVariant = "save" | "cancel" | "close" | "danger";

type ModalButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
    children: ReactNode;
    loading?: boolean;
    variant?: ModalButtonVariant;
};

export function ModalButton({ children, className, variant = "save", ...props }: ModalButtonProps) {
    const variantClassName = `modal-button modal-button--${variant}`;
    const nextClassName = className ? `${variantClassName} ${className}` : variantClassName;

    return (
        <Button className={nextClassName} {...props}>
            {children}
        </Button>
    );
}
