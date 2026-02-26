import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function Button({ children, className, type = "button", ...props }: ButtonProps) {
  const nextClassName = className ? `ui-button ${className}` : "ui-button";

  return (
    <button type={type} className={nextClassName} {...props}>
      {children}
    </button>
  );
}
