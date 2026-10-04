import { ApiError } from "./api";

const API_BASE_URL = "/api/data";

export interface DataTableMeta {
  name: string;
  label: string;
  row_count: number;
  filters: string[];
}

export interface DataTableResult {
  table: string;
  label: string;
  columns: string[];
  filters: string[];
  filter_options: Record<string, string[]>;
  rows: Record<string, unknown>[];
  page: number;
  page_size: number;
  total_rows: number;
  total_pages: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function fetchDataTables(): Promise<DataTableMeta[]> {
  const response = await fetch(`${API_BASE_URL}/tables`);

  let body: unknown = null;

  try {
    body = await response.json();
  } catch {
    // handled below
  }

  if (!response.ok) {
    throw new ApiError("Could not load database tables.", response.status);
  }

  if (!isRecord(body) || !Array.isArray(body.tables)) {
    throw new ApiError("Invalid table list response.", response.status);
  }

  return body.tables.flatMap((item) => {
    if (
      !isRecord(item)
      || typeof item.name !== "string"
      || typeof item.label !== "string"
      || typeof item.row_count !== "number"
    ) {
      return [];
    }

    const filters = Array.isArray(item.filters)
      ? item.filters.filter((f): f is string => typeof f === "string")
      : [];

    return [
      {
        name: item.name,
        label: item.label,
        row_count: item.row_count,
        filters,
      },
    ];
  });
}

export async function fetchDataTable(
  tableName: string,
  options: {
    page: number;
    pageSize: number;
    q?: string;
    filters: Record<string, string>;
  },
): Promise<DataTableResult> {
  const params = new URLSearchParams({
    page: String(options.page),
    page_size: String(options.pageSize),
  });

  if (options.q) {
    params.set("q", options.q);
  }

  for (const [key, value] of Object.entries(options.filters)) {
    if (value) {
      params.set(key, value);
    }
  }

  const response = await fetch(
    `${API_BASE_URL}/tables/${encodeURIComponent(tableName)}?${params}`,
  );

  let body: unknown = null;

  try {
    body = await response.json();
  } catch {
    // handled below
  }

  if (!response.ok) {
    throw new ApiError("Could not load table rows.", response.status);
  }

  if (!isRecord(body) || !Array.isArray(body.columns) || !Array.isArray(body.rows)) {
    throw new ApiError("Invalid table response.", response.status);
  }

  return body as unknown as DataTableResult;
}
