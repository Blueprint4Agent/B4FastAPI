type ToggleSwitchProps = {
    checked: boolean;
    disabled?: boolean;
    id?: string;
    label?: string;
    onCheckedChange: (checked: boolean) => void;
};

export function ToggleSwitch({
    checked,
    disabled = false,
    id,
    label,
    onCheckedChange,
}: ToggleSwitchProps) {
    return (
        <span className="ui-toggle">
            <button
                id={id}
                type="button"
                role="switch"
                aria-checked={checked}
                aria-label={label}
                className={`ui-toggle__track ${checked ? "ui-toggle__track--on" : "ui-toggle__track--off"}`}
                onClick={() => onCheckedChange(!checked)}
                disabled={disabled}
            >
                <span className="ui-toggle__thumb" />
            </button>
        </span>
    );
}
