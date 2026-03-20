type SpinnerProps = {
  className?: string;
  label?: string;
  size?: "sm" | "md" | "lg";
};

export function Spinner({ className, label, size = "md" }: SpinnerProps) {
  const nextClassName = className ? `ui-spinner ui-spinner--${size} ${className}` : `ui-spinner ui-spinner--${size}`;

  return (
    <span className={nextClassName} role="status" aria-live="polite" aria-label={label}>
      <span className="ui-spinner__ring" aria-hidden="true" />
      {label ? <span className="ui-spinner__label">{label}</span> : null}
    </span>
  );
}
