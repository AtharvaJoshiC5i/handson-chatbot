import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ChevronLeft,
  ChevronRight,
  CreditCard,
  Database,
  Headphones,
  RefreshCw,
  Search,
  Smartphone,
  Table2,
  Users,
} from "lucide-react";

import { StatusChip } from "../components/StatusChip";
import { statusVariantForValue } from "../utils/statusChip";
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

const TABLE_GROUPS: {
  id: string;
  label: string;
  icon: typeof Users;
  tables: string[];
}[] = [
  {
    id: "account",
    label: "Account & catalog",
    icon: Users,
    tables: [
      "customers",
      "plans",
      "subscriptions",
      "customer_payment_profiles",
      "account_credits",
      "devices",
    ],
  },
  {
    id: "usage",
    label: "Usage",
    icon: Smartphone,
    tables: ["usage"],
  },
  {
    id: "billing",
    label: "Billing & payments",
    icon: CreditCard,
    tables: ["bills", "bill_items", "payments"],
  },
  {
    id: "support",
    label: "Support",
    icon: Headphones,
    tables: ["support_tickets", "support_ticket_updates"],
  },
];

function tableIcon(tableName: string) {
  const group = TABLE_GROUPS.find((entry) =>
    entry.tables.includes(tableName),
  );
  return group?.icon ?? Table2;
}

function isStatusColumn(column: string): boolean {
  return /status|priority|category|item_type|payment_method|plan_type|account_status/i.test(
    column,
  );
}

interface DatabaseExplorerPageProps {
  customerId?: string;
}

export function DatabaseExplorerPage({
  customerId,
}: DatabaseExplorerPageProps) {
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
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tablesByName = useMemo(
    () => new Map(tables.map((table) => [table.name, table])),
    [tables],
  );

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

  useEffect(() => {
    if (!customerId || !selectedTable) {
      return;
    }

    const meta = tablesByName.get(selectedTable);
    if (!meta?.filters.includes("customer_id")) {
      return;
    }

    setFilterValues((current) => ({
      ...current,
      customer_id: customerId,
    }));
    setPage(1);
  }, [customerId, tablesByName, selectedTable]);

  const loadRows = useCallback(() => {
    if (!selectedTable) {
      return;
    }

    setRefreshing(true);
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
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [selectedTable, page, pageSize, search, filterValues]);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

  const handleTableChange = (tableName: string) => {
    setSelectedTable(tableName);
    setPage(1);
    setFilterValues(
      customerId && tablesByName.get(tableName)?.filters.includes("customer_id")
        ? { customer_id: customerId }
        : {},
    );
    setSearch("");
  };

  const activeFilters = result?.filters ?? [];
  const selectedMeta = selectedTable
    ? tablesByName.get(selectedTable)
    : undefined;

  return (
    <div className="db-explorer flex min-h-0 flex-1 flex-col">
      <header className="db-explorer-hero">
        <div className="db-explorer-hero-text">
          <div className="db-explorer-hero-title-row">
            <span className="db-explorer-hero-icon" aria-hidden>
              <Database size={18} strokeWidth={2} />
            </span>
            <div>
              <h1 className="db-explorer-title">Database viewer</h1>
              <p className="db-explorer-subtitle">
                Read-only nexatel.db — browse seeded records with search and
                filters.
              </p>
            </div>
          </div>
        </div>
        {selectedMeta && (
          <div className="db-explorer-hero-stat">
            <span className="db-explorer-hero-stat-label">Active table</span>
            <span className="db-explorer-hero-stat-value">
              {selectedMeta.label}
            </span>
            <span className="db-explorer-hero-stat-meta">
              {selectedMeta.row_count.toLocaleString("en-IN")} rows total
            </span>
          </div>
        )}
      </header>

      <div className="db-explorer-body">
        <aside className="db-explorer-sidebar" aria-label="Tables">
          {TABLE_GROUPS.map((group) => {
            const groupTables = group.tables
              .map((name) => tablesByName.get(name))
              .filter((table): table is DataTableMeta => Boolean(table));

            if (groupTables.length === 0) {
              return null;
            }

            const GroupIcon = group.icon;

            return (
              <section key={group.id} className="db-explorer-sidebar-group">
                <p className="db-explorer-sidebar-heading">
                  <GroupIcon size={12} aria-hidden />
                  {group.label}
                </p>
                <ul className="db-explorer-sidebar-list">
                  {groupTables.map((table) => {
                    const Icon = tableIcon(table.name);
                    const active = selectedTable === table.name;

                    return (
                      <li key={table.name}>
                        <button
                          type="button"
                          onClick={() => handleTableChange(table.name)}
                          className={[
                            "db-explorer-table-btn",
                            active ? "db-explorer-table-btn--active" : "",
                          ].join(" ")}
                        >
                          <Icon size={14} aria-hidden className="shrink-0" />
                          <span className="min-w-0 flex-1 truncate">
                            {table.label}
                          </span>
                          <span className="db-explorer-table-count">
                            {table.row_count.toLocaleString("en-IN")}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </aside>

        <div className="db-explorer-panel">
          <div className="db-explorer-toolbar">
            <label className="db-explorer-search">
              <Search size={15} aria-hidden className="db-explorer-search-icon" />
              <input
                type="search"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search IDs, names, references…"
                className="db-explorer-search-input"
              />
            </label>

            {activeFilters.map((filterKey) => {
              const options = result?.filter_options[filterKey] ?? [];

              return (
                <label key={filterKey} className="db-explorer-filter">
                  <span className="db-explorer-filter-label">
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
                    className="db-explorer-filter-select"
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

            <label className="db-explorer-filter">
              <span className="db-explorer-filter-label">Page size</span>
              <select
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number.parseInt(event.target.value, 10));
                  setPage(1);
                }}
                className="db-explorer-filter-select"
              >
                {[10, 25, 50, 100].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              onClick={() => loadRows()}
              disabled={refreshing}
              className="db-explorer-refresh"
              aria-label="Refresh table"
            >
              <RefreshCw
                size={15}
                className={refreshing ? "animate-spin" : ""}
                aria-hidden
              />
            </button>
          </div>

          {result && (
            <div className="db-explorer-meta">
              <span>
                Showing page {result.page} of {result.total_pages}
              </span>
              <span aria-hidden>·</span>
              <span>
                {result.total_rows.toLocaleString("en-IN")} matching rows
              </span>
              {customerId && filterValues.customer_id === customerId && (
                <>
                  <span aria-hidden>·</span>
                  <span>Scoped to {customerId}</span>
                </>
              )}
            </div>
          )}

          {error && (
            <p className="db-explorer-error" role="alert">
              {error}
            </p>
          )}

          <div className="db-explorer-table-wrap">
            {loading && !result ? (
              <p className="db-explorer-empty">Loading records…</p>
            ) : result && result.columns.length > 0 ? (
              <table className="db-explorer-table">
                <thead>
                  <tr>
                    {result.columns.map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {result.columns.map((column) => {
                        const raw = row[column];
                        const text =
                          raw === null || raw === undefined
                            ? "—"
                            : String(raw);

                        if (isStatusColumn(column) && text !== "—") {
                          const variant = statusVariantForValue(text);

                          return (
                            <td key={column}>
                              {variant ? (
                                <StatusChip label={text} variant={variant} />
                              ) : (
                                text
                              )}
                            </td>
                          );
                        }

                        return (
                          <td
                            key={column}
                            title={text}
                            data-mono={/id|reference|date|amount|price/i.test(
                              column,
                            )}
                          >
                            {text}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="db-explorer-empty">No rows match your filters.</p>
            )}
          </div>

          {result && result.total_pages > 1 && (
            <footer className="db-explorer-pagination">
              <button
                type="button"
                disabled={page <= 1 || refreshing}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                className="db-explorer-page-btn"
              >
                <ChevronLeft size={14} aria-hidden />
                Previous
              </button>
              <span className="db-explorer-page-label">
                Page {result.page} of {result.total_pages}
              </span>
              <button
                type="button"
                disabled={page >= result.total_pages || refreshing}
                onClick={() =>
                  setPage((current) =>
                    Math.min(result.total_pages, current + 1),
                  )
                }
                className="db-explorer-page-btn"
              >
                Next
                <ChevronRight size={14} aria-hidden />
              </button>
            </footer>
          )}
        </div>
      </div>
    </div>
  );
}
