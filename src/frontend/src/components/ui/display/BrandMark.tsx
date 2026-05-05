type BrandMarkProps = {
    className?: string;
};

// Replace brand assets under `/public/icons/b4a-mark*` to customize without code changes.
export function BrandMark({ className }: BrandMarkProps) {
    const nextClassName = className ? `brand-mark ${className}` : "brand-mark";

    return (
        <span className={nextClassName} aria-hidden="true">
            <picture className="brand-mark__asset brand-mark__asset--light">
                <source srcSet="/icons/b4a-mark.svg" type="image/svg+xml" />
                <img src="/icons/b4a-mark.png" alt="" />
            </picture>
            <picture className="brand-mark__asset brand-mark__asset--dark">
                <source srcSet="/icons/b4a-mark-dark.svg" type="image/svg+xml" />
                <img src="/icons/b4a-mark-dark.png" alt="" />
            </picture>
        </span>
    );
}
