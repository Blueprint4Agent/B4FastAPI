import { Check, X } from "lucide-react";

export type ValidationRule = {
    isValid: boolean;
    label: string;
};

type ValidationCardProps = {
    rules: ValidationRule[];
    title: string;
};

export function ValidationCard({ rules, title }: ValidationCardProps) {
    const isComplete = rules.length > 0 && rules.every((rule) => rule.isValid);

    return (
        <div
            className={`validation-card ${isComplete ? "validation-card--ok" : "validation-card--no"}`}
        >
            <div className="validation-card__title">{title}</div>
            <div className="validation-card__list">
                {rules.map((rule) => (
                    <div className="validation-card__item" key={rule.label}>
                        <span
                            className={`validation-card__mark ${
                                rule.isValid
                                    ? "validation-card__mark--ok"
                                    : "validation-card__mark--no"
                            }`}
                            aria-hidden="true"
                        >
                            {rule.isValid ? (
                                <Check className="validation-card__icon" strokeWidth={2.4} />
                            ) : (
                                <X className="validation-card__icon" strokeWidth={2.4} />
                            )}
                        </span>
                        <span className="validation-card__label">{rule.label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
