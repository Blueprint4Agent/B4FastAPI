import { ChevronLeft, ChevronRight } from "lucide-react";

type PaginationItem = number | "ellipsis";

type PaginationProps = {
    currentPage: number;
    totalPages: number;
    ariaLabel: string;
    previousLabel: string;
    nextLabel: string;
    onPageChange: (page: number) => void;
};

function buildPaginationItems(currentPage: number, totalPages: number): PaginationItem[] {
    if (totalPages <= 7) {
        return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    if (currentPage <= 4) {
        return [1, 2, 3, 4, 5, "ellipsis", totalPages];
    }

    if (currentPage >= totalPages - 3) {
        return [
            1,
            "ellipsis",
            totalPages - 4,
            totalPages - 3,
            totalPages - 2,
            totalPages - 1,
            totalPages,
        ];
    }

    return [1, "ellipsis", currentPage - 1, currentPage, currentPage + 1, "ellipsis", totalPages];
}

export function Pagination({
    currentPage,
    totalPages,
    ariaLabel,
    previousLabel,
    nextLabel,
    onPageChange,
}: PaginationProps) {
    if (totalPages <= 1) {
        return null;
    }

    const items = buildPaginationItems(currentPage, totalPages);

    return (
        <nav className="ui-pagination" aria-label={ariaLabel}>
            <button
                type="button"
                className="ui-pagination__button ui-pagination__button--icon"
                aria-label={previousLabel}
                disabled={currentPage === 1}
                onClick={() => {
                    onPageChange(Math.max(1, currentPage - 1));
                }}
            >
                <ChevronLeft aria-hidden="true" />
            </button>
            <ol className="ui-pagination__items">
                {items.map((item, index) => {
                    if (item === "ellipsis") {
                        return (
                            <li
                                // Pagination can render two ellipses; index keeps keys stable by position.
                                key={`ellipsis-${index}`}
                                className="ui-pagination__ellipsis"
                                aria-hidden="true"
                            >
                                ...
                            </li>
                        );
                    }

                    const isCurrent = item === currentPage;
                    return (
                        <li key={item}>
                            <button
                                type="button"
                                className={
                                    isCurrent
                                        ? "ui-pagination__button ui-pagination__button--active"
                                        : "ui-pagination__button"
                                }
                                aria-current={isCurrent ? "page" : undefined}
                                onClick={() => {
                                    onPageChange(item);
                                }}
                            >
                                {item}
                            </button>
                        </li>
                    );
                })}
            </ol>
            <button
                type="button"
                className="ui-pagination__button ui-pagination__button--icon"
                aria-label={nextLabel}
                disabled={currentPage === totalPages}
                onClick={() => {
                    onPageChange(Math.min(totalPages, currentPage + 1));
                }}
            >
                <ChevronRight aria-hidden="true" />
            </button>
        </nav>
    );
}
