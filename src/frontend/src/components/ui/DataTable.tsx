import type { ReactNode } from "react";

export type DataTableColumn<T> = {
    align?: "left" | "center" | "right";
    cellClassName?: string;
    header: string;
    headClassName?: string;
    id: string;
    render: (row: T) => ReactNode;
    width?: string;
};

type DataTableProps<T> = {
    columns: DataTableColumn<T>[];
    emptyText: string;
    onRowClick?: (row: T) => void;
    rows: T[];
    selectedRowKey?: string | number | null;
    rowKey: (row: T) => string | number;
};

export function DataTable<T>({
    columns,
    emptyText,
    onRowClick,
    rows,
    selectedRowKey = null,
    rowKey,
}: DataTableProps<T>) {
    return (
        <div className="ui-data-table-wrap">
            <table className="ui-data-table">
                <thead>
                    <tr>
                        {columns.map((column) => (
                            <th
                                key={column.id}
                                style={{ width: column.width }}
                                className={`ui-data-table__head ui-data-table__head--${
                                    column.align ?? "left"
                                }${column.headClassName ? ` ${column.headClassName}` : ""}`}
                                scope="col"
                            >
                                {column.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.length === 0 ? (
                        <tr>
                            <td className="ui-data-table__empty" colSpan={columns.length}>
                                {emptyText}
                            </td>
                        </tr>
                    ) : (
                        rows.map((row) => {
                            const key = rowKey(row);
                            const isSelected = selectedRowKey !== null && key === selectedRowKey;
                            const rowClassName = onRowClick
                                ? `ui-data-table__row ui-data-table__row--clickable${
                                      isSelected ? " ui-data-table__row--selected" : ""
                                  }`
                                : `ui-data-table__row${
                                      isSelected ? " ui-data-table__row--selected" : ""
                                  }`;

                            return (
                                <tr
                                    key={key}
                                    className={rowClassName}
                                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                                >
                                    {columns.map((column) => (
                                        <td
                                            key={column.id}
                                            className={`ui-data-table__cell ui-data-table__cell--${
                                                column.align ?? "left"
                                            }${column.cellClassName ? ` ${column.cellClassName}` : ""}`}
                                        >
                                            {column.render(row)}
                                        </td>
                                    ))}
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </table>
        </div>
    );
}
