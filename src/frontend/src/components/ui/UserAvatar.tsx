type UserAvatarProps = {
    className?: string;
    imageUrl?: string | null;
    label: string;
};

export function UserAvatar({ className, imageUrl, label }: UserAvatarProps) {
    const nextClassName = className ? `user-avatar ${className}` : "user-avatar";

    if (imageUrl) {
        return (
            <span className={nextClassName} aria-hidden="true">
                <img src={imageUrl} alt="" />
            </span>
        );
    }

    return (
        <span className={nextClassName} aria-hidden="true">
            <span>{label.slice(0, 1).toUpperCase()}</span>
        </span>
    );
}
