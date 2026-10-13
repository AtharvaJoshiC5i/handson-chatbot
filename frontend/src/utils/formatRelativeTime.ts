export function formatRelativeTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const diffMs = date.getTime() - Date.now();
  const absSeconds = Math.round(Math.abs(diffMs) / 1000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  if (absSeconds < 60) {
    return rtf.format(Math.round(diffMs / 1000), "second");
  }

  const absMinutes = Math.round(absSeconds / 60);

  if (absMinutes < 60) {
    return rtf.format(Math.round(diffMs / 60_000), "minute");
  }

  const absHours = Math.round(absMinutes / 60);

  if (absHours < 48) {
    return rtf.format(Math.round(diffMs / 3_600_000), "hour");
  }

  const absDays = Math.round(absHours / 24);

  if (absDays < 14) {
    return rtf.format(Math.round(diffMs / 86_400_000), "day");
  }

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}
