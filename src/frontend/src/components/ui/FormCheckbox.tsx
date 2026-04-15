import { useId } from "react";

type FormCheckboxProps = {
    checked: boolean;
    className?: string;
    id?: string;
    label: string;
    onCheckedChange: (checked: boolean) => void;
};

export function FormCheckbox({
    checked,
    className,
    id,
    label,
    onCheckedChange,
}: FormCheckboxProps) {
    const fieldId = useId();
    const inputId = id ?? fieldId;
    const nextClassName = className ? `checkbox ${className}` : "checkbox";

    return (
        <label className={nextClassName} htmlFor={inputId}>
            <input
                id={inputId}
                type="checkbox"
                checked={checked}
                onChange={(event) => onCheckedChange(event.target.checked)}
            />
            <span>{label}</span>
        </label>
    );
}
