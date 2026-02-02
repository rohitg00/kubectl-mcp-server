import React, { useState, useMemo } from "react";

export interface Column<T> {
  key: string;
  header: string;
  width?: string;
  sortable?: boolean;
  render?: (item: T, index: number) => React.ReactNode;
}

export interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
  loading?: boolean;
  sortable?: boolean;
  pagination?: {
    pageSize: number;
    currentPage: number;
    onPageChange: (page: number) => void;
  };
}

type SortDirection = "asc" | "desc";

export function Table<T extends Record<string, unknown>>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  emptyMessage = "No data available",
  loading = false,
  sortable = true,
  pagination,
}: TableProps<T>): React.ReactElement {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const sortedData = useMemo(() => {
    if (!sortKey) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison =
        typeof aVal === "string"
          ? aVal.localeCompare(String(bVal))
          : Number(aVal) - Number(bVal);

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [data, sortKey, sortDirection]);

  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    const start = (pagination.currentPage - 1) * pagination.pageSize;
    return sortedData.slice(start, start + pagination.pageSize);
  }, [sortedData, pagination]);

  const handleSort = (key: string) => {
    if (!sortable) return;

    const column = columns.find((c) => c.key === key);
    if (!column?.sortable && column?.sortable !== undefined) return;

    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const totalPages = pagination
    ? Math.ceil(data.length / pagination.pageSize)
    : 1;

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                style={{ width: column.width }}
                onClick={() =>
                  column.sortable !== false && handleSort(column.key)
                }
                className={sortable && column.sortable !== false ? "sortable" : ""}
              >
                <span className="header-content">
                  {column.header}
                  {sortKey === column.key && (
                    <span className="sort-indicator">
                      {sortDirection === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="loading-cell">
                <div className="loading-spinner" />
                <span>Loading...</span>
              </td>
            </tr>
          ) : paginatedData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-cell">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            paginatedData.map((item, index) => (
              <tr
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={onRowClick ? "clickable" : ""}
              >
                {columns.map((column) => (
                  <td key={column.key}>
                    {column.render
                      ? column.render(item, index)
                      : String(item[column.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {pagination && totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => pagination.onPageChange(pagination.currentPage - 1)}
            disabled={pagination.currentPage === 1}
          >
            Previous
          </button>
          <span className="page-info">
            Page {pagination.currentPage} of {totalPages}
          </span>
          <button
            onClick={() => pagination.onPageChange(pagination.currentPage + 1)}
            disabled={pagination.currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}

      <style>{`
        .table-container {
          overflow-x: auto;
        }

        .table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }

        .table th {
          text-align: left;
          padding: 10px 12px;
          background: var(--bg-tertiary);
          border-bottom: 1px solid var(--border);
          color: var(--text-secondary);
          font-weight: 600;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          user-select: none;
        }

        .table th.sortable {
          cursor: pointer;
        }

        .table th.sortable:hover {
          background: var(--border);
        }

        .header-content {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .sort-indicator {
          font-size: 10px;
          color: var(--primary);
        }

        .table td {
          padding: 10px 12px;
          border-bottom: 1px solid var(--border);
          color: var(--text);
        }

        .table tr:hover td {
          background: var(--bg-secondary);
        }

        .table tr.clickable {
          cursor: pointer;
        }

        .loading-cell,
        .empty-cell {
          text-align: center;
          padding: 40px !important;
          color: var(--text-muted);
        }

        .loading-cell {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid var(--border);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .pagination {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
          padding: 16px;
          border-top: 1px solid var(--border);
        }

        .pagination button {
          padding: 6px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text);
          cursor: pointer;
          transition: all 0.15s;
        }

        .pagination button:hover:not(:disabled) {
          background: var(--border);
          border-color: var(--border-hover);
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .page-info {
          color: var(--text-secondary);
          font-size: 13px;
        }
      `}</style>
    </div>
  );
}
