import { Check, Copy } from "lucide-react";

import { Button } from "../buttons/Button";

type CopyFieldProps = {
    value: string;
    inputAriaLabel: string;
    copyLabel: string;
    copiedLabel: string;
    copied: boolean;
    onCopy: () => void;
    disabled?: boolean;
};

export function CopyField({
    value,
    inputAriaLabel,
    copyLabel,
    copiedLabel,
    copied,
    onCopy,
    disabled = false,
}: CopyFieldProps) {
    return (
        <div className="copy-field">
            <input
                type="text"
                readOnly
                value={value}
                className="copy-field__input"
                aria-label={inputAriaLabel}
            />
            <Button
                type="button"
                className="copy-field__button"
                aria-label={copied ? copiedLabel : copyLabel}
                onClick={onCopy}
                disabled={disabled}
            >
                {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
            </Button>
        </div>
    );
}
