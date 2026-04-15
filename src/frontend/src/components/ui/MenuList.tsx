import type { LucideIcon } from "lucide-react";

import { Button } from "./Button";
import { PrimaryCard } from "./PrimaryCard";

export type MenuListItem<T extends string = string> = {
    icon: LucideIcon;
    key: T;
    label: string;
};

type MenuListProps<T extends string = string> = {
    activeKey: T;
    ariaLabel: string;
    className?: string;
    items: readonly MenuListItem<T>[];
    onSelect: (key: T) => void;
};

export function MenuList<T extends string = string>({
    activeKey,
    ariaLabel,
    className,
    items,
    onSelect,
}: MenuListProps<T>) {
    const rootClassName = className ? `menu-list ${className}` : "menu-list";

    return (
        <PrimaryCard className={rootClassName}>
            <nav className="menu-list__items" aria-label={ariaLabel}>
                {items.map(({ icon: Icon, key, label }) => {
                    const isActive = activeKey === key;
                    const itemClassName = isActive
                        ? "menu-list__item menu-list__item--active"
                        : "menu-list__item";

                    return (
                        <Button
                            key={key}
                            className={itemClassName}
                            onClick={() => onSelect(key)}
                            aria-current={isActive ? "page" : undefined}
                        >
                            <span className="menu-list__item-icon" aria-hidden="true">
                                <Icon />
                            </span>
                            <span className="menu-list__item-label">{label}</span>
                        </Button>
                    );
                })}
            </nav>
        </PrimaryCard>
    );
}
