import type {
  AccountSnapshot,
  CustomerProfile,
  DemoCustomer,
} from "../types/account";
import type {
  ChatOption,
  ChatPresentation,
  ChatResponse,
  ChatResponseStatus,
  ComparisonColumn,
  ComparisonRow,
  Customer360Table,
  KeyValueItem,
  ListItem,
  PlanRecommendationPlan,
  PlanRecommendationPresentation,
  SummarySection,
  TableColumn,
  TimeSeriesPoint,
  TimeSeriesPresentation,
} from "../types/chat";

const API_BASE_URL = "/api";

const VALID_STATUSES: ChatResponseStatus[] = [
  "VERIFIED",
  "NOT_FOUND",
  "AMBIGUOUS",
  "UNSUPPORTED",
  "DATABASE_ERROR",
  "VALIDATION_ERROR",
  "ACCESS_DENIED",
  "API_ERROR",
];

export class ApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

export interface ChatStreamHandlers {
  onMetadata: (response: ChatResponse) => void;
  onText: (text: string) => void;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNullableString(value: unknown): value is string | null | undefined {
  return value === undefined || value === null || typeof value === "string";
}

function isChatStatus(value: unknown): value is ChatResponseStatus {
  return (
    typeof value === "string" &&
    VALID_STATUSES.includes(value as ChatResponseStatus)
  );
}

function parseOptions(value: unknown): ChatOption[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (
      !isRecord(item) ||
      !isString(item.label) ||
      !isString(item.message)
    ) {
      return [];
    }

    return [
      {
        label: item.label,
        message: item.message,
      },
    ];
  });
}

function parseKeyValueItems(value: unknown): KeyValueItem[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const items: KeyValueItem[] = [];

  for (const item of value) {
    if (
      !isRecord(item) ||
      !isString(item.label) ||
      !isString(item.value)
    ) {
      return null;
    }

    items.push({
      label: item.label,
      value: item.value,
    });
  }

  return items;
}

function parseComparisonColumns(
  value: unknown,
): ComparisonColumn[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const columns: ComparisonColumn[] = [];

  for (const column of value) {
    if (
      !isRecord(column) ||
      !isString(column.key) ||
      !isString(column.label)
    ) {
      return null;
    }

    columns.push({
      key: column.key,
      label: column.label,
    });
  }

  return columns;
}

function parseComparisonRows(
  value: unknown,
): ComparisonRow[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const rows: ComparisonRow[] = [];

  for (const row of value) {
    if (
      !isRecord(row) ||
      !isString(row.label) ||
      !isRecord(row.values)
    ) {
      return null;
    }

    const values: Record<string, string> = {};

    for (const [key, cellValue] of Object.entries(row.values)) {
      if (!isString(cellValue)) {
        return null;
      }

      values[key] = cellValue;
    }

    rows.push({
      label: row.label,
      values,
    });
  }

  return rows;
}

function parseListItems(value: unknown): ListItem[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const items: ListItem[] = [];

  for (const item of value) {
    if (
      !isRecord(item) ||
      !isString(item.label) ||
      !isString(item.value) ||
      !isNullableString(item.detail)
    ) {
      return null;
    }

    items.push({
      label: item.label,
      value: item.value,
      detail: item.detail,
    });
  }

  return items;
}

function parseTableColumns(value: unknown): TableColumn[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const columns: TableColumn[] = [];

  for (const column of value) {
    if (
      !isRecord(column) ||
      !isString(column.key) ||
      !isString(column.label)
    ) {
      return null;
    }

    const align = column.align;

    if (
      align !== undefined &&
      align !== "left" &&
      align !== "right"
    ) {
      return null;
    }

    columns.push({
      key: column.key,
      label: column.label,
      align,
    });
  }

  return columns;
}

function parseTableRows(
  value: unknown,
): Record<string, string>[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const rows: Record<string, string>[] = [];

  for (const row of value) {
    if (!isRecord(row)) {
      return null;
    }

    const parsedRow: Record<string, string> = {};

    for (const [key, cellValue] of Object.entries(row)) {
      if (!isString(cellValue)) {
        return null;
      }

      parsedRow[key] = cellValue;
    }

    rows.push(parsedRow);
  }

  return rows;
}

function parseTimeSeriesPoints(
  value: unknown,
): TimeSeriesPoint[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const points: TimeSeriesPoint[] = [];
  for (const point of value) {
    if (
      !isRecord(point) ||
      !isString(point.period) ||
      typeof point.value !== "number" ||
      !Number.isFinite(point.value) ||
      !isNullableString(point.detail)
    ) {
      return null;
    }

    points.push({
      period: point.period,
      value: point.value,
      detail: point.detail,
    });
  }

  return points;
}

function parseSummarySections(
  value: unknown,
): SummarySection[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const sections: SummarySection[] = [];

  for (const section of value) {
    if (
      !isRecord(section) ||
      !isString(section.label) ||
      !isString(section.primary) ||
      !isNullableString(section.secondary)
    ) {
      return null;
    }

    sections.push({
      label: section.label,
      primary: section.primary,
      secondary: section.secondary,
    });
  }

  return sections;
}

function parseCustomer360Tables(
  value: unknown,
): Customer360Table[] | null {
  if (!Array.isArray(value)) {
    return null;
  }

  const tables: Customer360Table[] = [];

  for (const table of value) {
    if (
      !isRecord(table) ||
      !isString(table.title)
    ) {
      return null;
    }

    const columns = parseTableColumns(
      table.columns,
    );
    const rows = parseTableRows(
      table.rows,
    );

    if (!columns || !rows) {
      return null;
    }

    tables.push({
      title: table.title,
      columns,
      rows,
    });
  }

  return tables;
}

function parsePlanRecommendationPlan(
  value: unknown,
): PlanRecommendationPlan | null {
  if (!isRecord(value) || !isString(value.plan_name)) {
    return null;
  }

  const monthlyPrice = value.monthly_price;
  const dataLimit = value.data_limit_gb;

  return {
    plan_name: value.plan_name,
    monthly_price:
      typeof monthlyPrice === "number" && Number.isFinite(monthlyPrice)
        ? monthlyPrice
        : null,
    data_limit_gb:
      typeof dataLimit === "number" && Number.isFinite(dataLimit)
        ? dataLimit
        : null,
  };
}

function parsePlanRecommendation(
  value: Record<string, unknown>,
  title: string | null | undefined,
): PlanRecommendationPresentation | null {
  const current = parsePlanRecommendationPlan(value.current);

  if (!current || !isString(value.recommendation_status)) {
    return null;
  }

  const recommended = value.recommended === null
    || value.recommended === undefined
    ? null
    : parsePlanRecommendationPlan(value.recommended);

  if (value.recommended !== null && value.recommended !== undefined && !recommended) {
    return null;
  }

  const reasons: string[] = [];
  if (Array.isArray(value.reasons)) {
    for (const reason of value.reasons) {
      if (!isString(reason)) {
        return null;
      }
      reasons.push(reason);
    }
  }

  const avg = value.average_monthly_data_gb;
  const months = value.months_sampled;
  const utilization = value.utilization_percent;
  const savings = value.estimated_monthly_savings;

  return {
    type: "plan_recommendation",
    title,
    recommendation_status: value.recommendation_status,
    current,
    recommended,
    average_monthly_data_gb:
      typeof avg === "number" && Number.isFinite(avg) ? avg : null,
    months_sampled:
      typeof months === "number" && Number.isFinite(months) ? months : null,
    utilization_percent:
      typeof utilization === "number" && Number.isFinite(utilization)
        ? utilization
        : null,
    estimated_monthly_savings:
      typeof savings === "number" && Number.isFinite(savings) ? savings : null,
    reasons,
  };
}

function parsePresentation(value: unknown): ChatPresentation | null {
  if (!isRecord(value) || !isString(value.type)) {
    return null;
  }

  const title = isNullableString(value.title)
    ? value.title
    : null;

  switch (value.type) {
    case "key_value": {
      const items = parseKeyValueItems(value.items);

      if (!items) {
        return null;
      }

      return {
        type: "key_value",
        title,
        items,
      };
    }

    case "comparison": {
      const columns = parseComparisonColumns(value.columns);
      const rows = parseComparisonRows(value.rows);

      if (!columns || !rows) {
        return null;
      }

      return {
        type: "comparison",
        title,
        columns,
        rows,
      };
    }

    case "list": {
      const items = parseListItems(value.items);

      if (!items) {
        return null;
      }

      return {
        type: "list",
        title,
        items,
      };
    }

    case "table": {
      const columns = parseTableColumns(value.columns);
      const rows = parseTableRows(value.rows);

      if (!columns || !rows) {
        return null;
      }

      return {
        type: "table",
        title,
        columns,
        rows,
      };
    }

    case "time_series": {
      const points = parseTimeSeriesPoints(value.points);
      const chartType = value.chart_type;
      const valueFormat = value.value_format;

      if (
        !points ||
        (chartType !== "line" && chartType !== "bar") ||
        !isString(value.unit) ||
        (valueFormat !== "number" && valueFormat !== "inr")
      ) {
        return null;
      }

      const presentation: TimeSeriesPresentation = {
        type: "time_series",
        title,
        chart_type: chartType,
        unit: value.unit,
        value_format: valueFormat,
        points,
      };

      return presentation;
    }

    case "summary": {
      const sections = parseSummarySections(value.sections);

      if (!sections) {
        return null;
      }

      return {
        type: "summary",
        title,
        sections,
      };
    }

    case "plan_recommendation": {
      const presentation = parsePlanRecommendation(value, title);

      if (!presentation) {
        return null;
      }

      return presentation;
    }

    case "customer_360": {
      const sections = parseSummarySections(
        value.sections,
      );
      const tables = parseCustomer360Tables(
        value.tables,
      );

      if (!sections) {
        return null;
      }

      return {
        type: "customer_360",
        title,
        sections,
        tables: tables ?? [],
      };
    }

    default:
      /*
       * Unknown future presentation types intentionally fall back
       * to the conversational message.
       */
      return null;
  }
}

function parseChatResponse(
  responseBody: unknown,
  statusCode: number,
): ChatResponse {
  if (
    !isRecord(responseBody) ||
    !isString(responseBody.message) ||
    !isChatStatus(responseBody.status)
  ) {
    throw new ApiError(
      "The backend returned an invalid response.",
      statusCode,
    );
  }

  const source =
    responseBody.source === null || responseBody.source === undefined
      ? null
      : isString(responseBody.source)
        ? responseBody.source
        : null;

  return {
    message: responseBody.message,
    status: responseBody.status,
    source,
    presentation: parsePresentation(responseBody.presentation),
    options: parseOptions(responseBody.options),
  };
}

function getErrorMessage(
  responseBody: unknown,
  statusCode: number,
): string {
  if (!isRecord(responseBody)) {
    return statusCode === 404
      ? "The chat endpoint was not found. Check that the backend is running on port 8001."
      : "The request could not be completed.";
  }

  if (typeof responseBody.detail === "string") {
    return responseBody.detail;
  }

  if (typeof responseBody.message === "string") {
    return responseBody.message;
  }

  if (Array.isArray(responseBody.detail)) {
    const validationMessages = responseBody.detail
      .filter(
        (item): item is { msg: string } =>
          isRecord(item) && typeof item.msg === "string",
      )
      .map((item) => item.msg);

    if (validationMessages.length > 0) {
      return validationMessages.join(" ");
    }
  }

  return statusCode === 404
    ? "The chat endpoint was not found. Check that the backend is running on port 8001."
    : "The request could not be completed.";
}

export async function sendChatMessage(
  customerId: string,
  message: string,
  conversationId: string,
): Promise<ChatResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Customer-ID": customerId,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
  } catch {
    throw new ApiError(
      "The NexaTel backend is unavailable. Make sure it is running on port 8001.",
      0,
    );
  }

  let responseBody: unknown = null;

  try {
    responseBody = await response.json();
  } catch {
    // Some proxies return an empty body for network-level errors.
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  return parseChatResponse(
    responseBody,
    response.status,
  );
}

export async function resetConversationContext(
  customerId: string,
  conversationId: string,
): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/chat/reset`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Customer-ID": customerId,
      },
      body: JSON.stringify({
        conversation_id: conversationId,
      }),
    });
  } catch {
    // A fresh ID still isolates the next chat turn if reset is unreachable.
  }
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch("/health");

    return response.ok;
  } catch {
    return false;
  }
}

function parseCustomerProfile(
  responseBody: unknown,
  statusCode: number,
): CustomerProfile {
  if (
    !isRecord(responseBody)
    || !isString(responseBody.name)
    || !isString(responseBody.phone_masked)
    || !isString(responseBody.city)
    || !isString(responseBody.service_address_line)
    || !isString(responseBody.account_status)
  ) {
    throw new ApiError(
      "The backend returned an invalid customer profile.",
      statusCode,
    );
  }

  return {
    name: responseBody.name,
    phone_masked: responseBody.phone_masked,
    city: responseBody.city,
    service_address_line: responseBody.service_address_line,
    account_status: responseBody.account_status,
  };
}

function parseAccountSnapshot(
  responseBody: unknown,
  statusCode: number,
): AccountSnapshot {
  if (!isRecord(responseBody) || !isString(responseBody.customer_id)) {
    throw new ApiError(
      "The backend returned an invalid account snapshot.",
      statusCode,
    );
  }

  return responseBody as unknown as AccountSnapshot;
}

async function fetchWithCustomerHeader(
  customerId: string,
  path: string,
  signal?: AbortSignal,
): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "X-Customer-ID": customerId,
      },
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new ApiError(
      "The NexaTel backend is unavailable. Make sure it is running on port 8001.",
      0,
    );
  }
}

export async function getCustomerProfile(
  customerId: string,
  signal?: AbortSignal,
): Promise<CustomerProfile> {
  const response = await fetchWithCustomerHeader(
    customerId,
    "/chat/profile",
    signal,
  );

  let responseBody: unknown = null;

  try {
    responseBody = await response.json();
  } catch {
    // Leave the response invalid so it is reported below.
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  return parseCustomerProfile(
    responseBody,
    response.status,
  );
}

export async function getCustomerName(
  customerId: string,
  signal?: AbortSignal,
): Promise<string> {
  const profile = await getCustomerProfile(
    customerId,
    signal,
  );

  return profile.name;
}

export async function getAccountSnapshot(
  customerId: string,
  signal?: AbortSignal,
): Promise<AccountSnapshot> {
  const response = await fetchWithCustomerHeader(
    customerId,
    "/chat/account-snapshot",
    signal,
  );

  let responseBody: unknown = null;

  try {
    responseBody = await response.json();
  } catch {
    // Leave the response invalid so it is reported below.
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  return parseAccountSnapshot(
    responseBody,
    response.status,
  );
}

export async function getDemoCustomers(
  signal?: AbortSignal,
): Promise<DemoCustomer[]> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/chat/demo-customers`, {
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new ApiError(
      "The NexaTel backend is unavailable. Make sure it is running on port 8001.",
      0,
    );
  }

  let responseBody: unknown = null;

  try {
    responseBody = await response.json();
  } catch {
    // Leave the response invalid so it is reported below.
  }

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  if (
    !isRecord(responseBody)
    || !Array.isArray(responseBody.customers)
  ) {
    throw new ApiError(
      "The backend returned an invalid demo customer list.",
      response.status,
    );
  }

  return responseBody.customers.flatMap((item) => {
    if (
      !isRecord(item)
      || !isString(item.customer_id)
      || !isString(item.name)
      || !isString(item.phone_masked)
    ) {
      return [];
    }

    return [
      {
        customer_id: item.customer_id,
        name: item.name,
        phone_masked: item.phone_masked,
      },
    ];
  });
}

export async function streamChatMessage(
  customerId: string,
  message: string,
  conversationId: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "X-Customer-ID": customerId,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new ApiError(
      "The NexaTel backend is unavailable. Make sure it is running on port 8001.",
      0,
    );
  }

  if (!response.ok) {
    let responseBody: unknown = null;

    try {
      responseBody = await response.json();
    } catch {
      // Some proxies return an empty body for network-level errors.
    }

    throw new ApiError(
      getErrorMessage(responseBody, response.status),
      response.status,
    );
  }

  if (!response.body) {
    throw new ApiError(
      "The support response could not be streamed.",
      response.status,
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let receivedMetadata = false;
  let receivedDone = false;

  const processEvent = (rawEvent: string) => {
    let eventName = "message";
    const dataLines: string[] = [];

    for (const line of rawEvent.split(/\r?\n/)) {
      if (!line || line.startsWith(":")) {
        continue;
      }

      const separator = line.indexOf(":");
      const field = separator < 0 ? line : line.slice(0, separator);
      const value = separator < 0 ? "" : line.slice(separator + 1).replace(/^ /, "");

      if (field === "event") {
        eventName = value;
      } else if (field === "data") {
        dataLines.push(value);
      }
    }

    if (dataLines.length === 0) {
      return;
    }

    let payload: unknown;

    try {
      payload = JSON.parse(dataLines.join("\n"));
    } catch {
      throw new ApiError(
        "The support service sent an invalid streaming event.",
        response.status,
      );
    }

    if (eventName === "metadata") {
      handlers.onMetadata(parseChatResponse(payload, response.status));
      receivedMetadata = true;
      return;
    }

    if (eventName === "delta") {
      if (!isRecord(payload) || !isString(payload.text)) {
        throw new ApiError(
          "The support service sent an invalid text update.",
          response.status,
        );
      }

      handlers.onText(payload.text);
      return;
    }

    if (eventName === "error") {
      throw new ApiError(
        isRecord(payload) && isString(payload.message)
          ? payload.message
          : "The support response was interrupted.",
        response.status,
      );
    }

    if (eventName === "done") {
      receivedDone = true;
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });

      let boundary = buffer.indexOf("\n\n");
      while (boundary >= 0) {
        processEvent(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");
      }

      if (done) {
        break;
      }
    }

    if (buffer.trim()) {
      processEvent(buffer);
    }
  } finally {
    reader.releaseLock();
  }

  if (!receivedMetadata || !receivedDone) {
    throw new ApiError(
      "The support response ended before it was complete.",
      response.status,
    );
  }
}