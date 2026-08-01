import { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

/* Phase 01B — sticky-header data table with sortable columns. Used by the
   transaction feed / audit log / agent list. Column defs:
     { key, header, render?(row), sortValue?(row), className }
   Rows are objects. Sort is controlled internally; pass initialSortKey if
   you want a default order. */

function getSortValue(row, col) {
  if (col.sortValue) return col.sortValue(row);
  const v = row[col.key];
  if (v == null) return '';
  return typeof v === 'number' ? v : String(v);
}

export function DataTable({
  columns,
  rows,
  initialSortKey,
  initialSortDir,
  rowKey = (r, i) => r.id ?? i,
  onRowClick,
  emptyMessage = 'No data',
  className,
}) {
  const [sortKey, setSortKey] = useState(initialSortKey);
  const [sortDir, setSortDir] = useState(initialSortDir ?? 'asc');

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    const col = columns.find((c) => c.key === sortKey);
    if (!col) return rows;
    const mul = sortDir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = getSortValue(a, col);
      const bv = getSortValue(b, col);
      if (av < bv) return -1 * mul;
      if (av > bv) return 1 * mul;
      return 0;
    });
  }, [rows, columns, sortKey, sortDir]);

  const handleSort = (col) => {
    if (sortKey === col.key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col.key);
      setSortDir('asc');
    }
  };

  return (
    <div className={cn('overflow-auto border border-border rounded-xl bg-card', className)}>
      <table className="w-full border-collapse">
        <thead className="sticky top-0 z-10 bg-card border-b border-border">
          <tr>
            {columns.map((col) => {
              const active = sortKey === col.key;
              return (
                <th
                  key={col.key}
                  onClick={col.sortable === false ? undefined : () => handleSort(col)}
                  className={cn(
                    'text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3.5 py-2.5',
                    col.sortable !== false && 'cursor-pointer select-none hover:text-foreground',
                    col.headClassName,
                  )}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {col.sortable !== false && (
                      active ? (
                        sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                      ) : (
                        <ChevronsUpDown className="h-3 w-3 opacity-50" />
                      )
                    )}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3.5 py-8 text-center text-sm text-muted-foreground">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedRows.map((row, i) => (
              <tr
                key={rowKey(row, i)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  'border-b border-border/60 last:border-0 transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-muted/50',
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn('px-3.5 py-2.5 text-sm text-foreground', col.className)}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
