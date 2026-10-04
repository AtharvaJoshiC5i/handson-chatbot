export type StatusVariant =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

const STATUS_MAP: Record<string, StatusVariant> = {
  ACTIVE: "success",
  PAID: "success",
  SUCCESS: "success",
  COMPLETED: "success",
  VERIFIED: "success",
  OPEN: "info",
  PENDING: "warning",
  UNPAID: "warning",
  DUE: "warning",
  OVERDUE: "danger",
  FAILED: "danger",
  DECLINED: "danger",
  SUSPENDED: "danger",
  CANCELLED: "neutral",
  CLOSED: "neutral",
  RESOLVED: "success",
};

export function statusVariantForValue(
  value: string,
): StatusVariant | null {
  const token = value.trim().split(/\s+/)[0]?.toUpperCase();

  if (!token) {
    return null;
  }

  if (STATUS_MAP[token]) {
    return STATUS_MAP[token];
  }

  const upper = value.toUpperCase();

  if (upper.includes("OVERDUE")) {
    return "danger";
  }

  if (upper.includes("FAILED")) {
    return "danger";
  }

  if (upper.includes("UNPAID")) {
    return "warning";
  }

  if (upper.includes("PAID")) {
    return "success";
  }

  return null;
}

export function isStatusLabel(label: string): boolean {
  const normalized = label.toLowerCase();

  return (
    normalized.includes("status")
    || normalized.includes("state")
    || normalized.endsWith(" outcome")
  );
}
