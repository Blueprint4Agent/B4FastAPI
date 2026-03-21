import { useEffect, useRef, useState } from "react";

type DropdownItem = {
  id: string;
  label: string;
};

type DropdownMenuProps = {
  className?: string;
  items: DropdownItem[];
  label?: string;
  onSelect?: (id: string) => void;
  triggerLabel: string;
};

export function DropdownMenu({
  className,
  items,
  label = "Dropdown menu",
  onSelect,
  triggerLabel
}: DropdownMenuProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const nextClassName = className ? `ui-dropdown ${className}` : "ui-dropdown";

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div className={nextClassName} ref={rootRef}>
      <button
        type="button"
        className="ui-dropdown__trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
      >
        {triggerLabel}
      </button>
      {open ? (
        <div className="ui-dropdown__menu" role="menu" aria-label={label}>
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className="ui-dropdown__item"
              role="menuitem"
              onClick={() => {
                onSelect?.(item.id);
                setOpen(false);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
