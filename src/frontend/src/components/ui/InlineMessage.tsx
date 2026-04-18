type InlineMessageTone = "error" | "info";

type InlineMessageProps = {
    children: string;
    tone?: InlineMessageTone;
};

export function InlineMessage({ children, tone = "error" }: InlineMessageProps) {
    return <p className={`ui-inline-message ui-inline-message--${tone}`}>{children}</p>;
}
