import { useId } from "react";
import type { InputHTMLAttributes } from "react";

type InputFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange"> & {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
};

export function InputField({
  label,
  value,
  onValueChange,
  id,
  className,
  ...inputProps
}: InputFieldProps) {
  const fieldId = useId();
  const inputId = id ?? fieldId;
  const nextClassName = className ? `form-field ${className}` : "form-field";

  return (
    <label className={nextClassName} htmlFor={inputId}>
      {label}
      <input
        id={inputId}
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        {...inputProps}
      />
    </label>
  );
}
