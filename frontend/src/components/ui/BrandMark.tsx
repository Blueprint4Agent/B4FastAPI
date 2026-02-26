type BrandMarkProps = {
  className?: string;
};

// Replace `/public/icons/b4a-mark.svg` to customize brand icon without code changes.
export function BrandMark({ className }: BrandMarkProps) {
  const nextClassName = className ? `brand-mark ${className}` : "brand-mark";

  return (
    <span className={nextClassName} aria-hidden="true">
      <img src="/icons/b4a-mark.svg" alt="" />
    </span>
  );
}
