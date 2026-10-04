import { useCallback, useEffect, useState } from "react";

import { ChevronLeft, ChevronRight, Database, Search } from "lucide-react";

import {
  fetchDataTable,
  fetchDataTables,
  type DataTableMeta,
  type DataTableResult,
} from "../services/dataExplorerApi";

const FILTER_LABELS: Record<string, string> = {
  customer_id: "Customer ID",
  status: "Status",
  account_status: "Account status",
  city: "City",
  plan_type: "Plan type",
  subscription_id: "Subscription ID",
  bill_id: "Bill ID",
  item_type: "Item type",
  payment_method: "Payment method",
  category: "Category",
  priority: "Priority",
  ticket_id: "Ticket ID",
};

export function DatabaseExplorerPage() {
  const [tables, setTables] = useState<DataTableMeta[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [result, setResult] = useState<DataTableResult | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState<
    Record<string, string>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchDataTables()
      .then((list) => {
        setTables(list);
        if (list.length > 0) {
          setSelectedTable(list[0].name);
        }
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : "Could not load tables.",
        );
      });
  }, []);

  const loadRows = useCallback(() => {
    if (!selectedTable) {
      return;
    }

    setLoading(true);
    setError(null);

    void fetchDataTable(selectedTable, {
      page,
      pageSize,
      q: search || undefined,
      filters: filterValues,
    })
      .then(setResult)
      .catch((err: unknown) => {
        setResult(null);
        setError(
          err instanceof Error
            ? err.message
            : "Could not load rows.",
        );
      })
      .finally(() => setLoading(false));
  }, [selectedTable, page, pageSize, search, filterValues]);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

  const handleTableChange = (tableName: string) => {
    setSelectedTable(tableName);
    setPage(1);
    setFilterValues({});
    setSearch("");
  };

  const activeFilters = result?.filters ?? [];

  return (
    <div className="chat-canvas flex min-h-0 flex-1 flex-col">
      <div className="surface-header border-b border-[var(--color-line)] px-5 py-4 sm:px-6">
        <div className="flex items-center gap-2">
          <Database
            size={18}
            className="text-[#3d6b55]"
            aria-hidden="true"
          />
          <h1 className="text-[15px] font-semibold text-[#23352e]">
            Database explorer
          </h1>
        </div>
        <p className="mt-1 text-[12px] text-[#74837a]">
          Read-only view of seeded NexaTel data for demos.
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden p-4 sm:p-6 lg:flex-row">
        <aside
          className="flex shrink-0 flex-col gap-1 overflow-y-auto rounded-lg border border-[#e2e8e3] bg-white p-2 lg:w-52"
          aria-label="Tables"
        >
          {tables.map((table) => (
            <button
              key={table.name}
              type="button"
              onClick={() => handleTableChange(table.name)}
              className={[
                "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-[12px]",
                selectedTable === table.name
                  ? "bg-[#edf3ef] font-semibold text-[#264a38]"
                  : "text-[#52665a] hover:bg-[#f5f8f5]",
              ].join(" ")}
            >
              <span>{table.label}</span>
              <span className="tabular-nums text-[10px] text-[#96a198]">
                {table.row_count}
              </span>
            </button>
          ))}
        </aside>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-[#e2e8e3] bg-white">
          <div className="space-y-3 border-b border-[#edf1ed] p-4">
            <div className="flex flex-wrap items-end gap-3">
              <label className="flex min-w-[200px] flex-1 flex-col gap-1">
                <span className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
                  Search
                </span>
                <div className="relative">
                  <Search
                    size={14}
                    className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#96a198]"
                    aria-hidden="true"
                  />
                  <input
                    type="search"
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setPage(1);
                    }}
                    placeholder="ID, name, reference…"
                    className="h-9 w-full rounded-md border border-[#dce5de] bg-[#fbfcfb] pl-8 pr-3 text-[12px] outline-none focus:border-[#71927d]"
                  />
                </div>
              </label>

              {activeFilters.map((filterKey) => {
                const options =
                  result?.filter_options[filterKey] ?? [];

                return (
                  <label
                    key={filterKey}
                    className="flex min-w-[140px] flex-col gap-1"
                  >
                    <span className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
                      {FILTER_LABELS[filterKey] ?? filterKey}
                    </span>
                    <select
                      value={filterValues[filterKey] ?? ""}
                      onChange={(event) => {
                        setFilterValues((current) => ({
                          ...current,
                          [filterKey]: event.target.value,
                        }));
                        setPage(1);
                      }}
                      className="h-9 rounded-md border border-[#dce5de] bg-[#fbfcfb] px-2 text-[12px] outline-none focus:border-[#71927d]"
                    >
                      <option value="">All</option>
                      {options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                );
              })}

              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
                  Rows per page
                </span>
                <select
                  value={pageSize}
                  onChange={(event) => {
                    setPageSize(Number.parseInt(event.target.value, 10));
                    setPage(1);
                  }}
                  className="h-9 rounded-md border border-[#dce5de] bg-[#fbfcfb] px-2 text-[12px]"
                >
                  {[10, 25, 50, 100].map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {result && (
              <p className="text-[11px] text-[#96a198]">
                {result.total_rows.toLocaleString()} rows
                {Object.values(filterValues).some(Boolean) || search
                  ? " (filtered)"
                  : ""}
              </p>
            )}
          </div>

          {error && (
            <p className="px-4 py-3 text-[12px] text-[#874b43]" role="alert">
              {error}
            </p>
          )}

          <div className="min-h-0 flex-1 overflow-auto">
            {loading && !result ? (
              <p className="p-6 text-[12px] text-[#96a198]">Loading…</p>
            ) : result && result.columns.length > 0 ? (
              <table className="w-full min-w-max border-collapse text-left text-[11px]">
                <thead className="sticky top-0 bg-[#f6f8f6] shadow-[0_1px_0_#e5ebe6]">
                  <tr>
                    {result.columns.map((column) => (
                      <th
                        key={column}
                        className="whitespace-nowrap px-3 py-2.5 font-semibold text-[#65766a]"
                      >
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, rowIndex) => (
                    <tr
                      key={rowIndex}
                      className="border-t border-[#edf1ed] hover:bg-[#fafcfb]"
                    >
                      {result.columns.map((column) => (
                        <td
                          key={column}
                          className="max-w-[240px] truncate whitespace-nowrap px-3 py-2 text-[#34483b]"
                          title={String(row[column] ?? "")}
                        >
                          {row[column] === null || row[column] === undefined
                            ? "—"
                            : String(row[column])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="p-6 text-[12px] text-[#96a198]">No rows found.</p>
            )}
          </div>

          {result && result.total_pages > 1 && (
            <div className="flex items-center justify-between gap-3 border-t border-[#edf1ed] px-4 py-3">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                className="inline-flex items-center gap-1 rounded-md border border-[#dce5de] px-3 py-1.5 text-[11px] font-medium disabled:opacity-40"
              >
                <ChevronLeft size={14} aria-hidden="true" />
                Previous
              </button>
              <span className="text-[11px] tabular-nums text-[#74837a]">
                Page {result.page} of {result.total_pages}
              </span>
              <button
                type="button"
                disabled={page >= result.total_pages || loading}
                onClick={() =>
                  setPage((current) =>
                    Math.min(result.total_pages, current + 1),
                  )
                }
                className="inline-flex items-center gap-1 rounded-md border border-[#dce5de] px-3 py-1.5 text-[11px] font-medium disabled:opacity-40"
              >
                Next
                <ChevronRight size={14} aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
