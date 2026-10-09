import type { ComparisonPresentation } from "../types/chat";

function parseInr(value: string): number | null {
  const cleaned = value.replace(/[^\d.-]/g, "");

  if (!cleaned) {
    return null;
  }

  const parsed = Number.parseFloat(cleaned);

  return Number.isFinite(parsed) ? parsed : null;
}

interface ComparisonHeroProps {
  presentation: ComparisonPresentation;
}

export function ComparisonHero({
  presentation,
}: ComparisonHeroProps) {
  if (presentation.columns.length !== 2) {
    return null;
  }

  const amountRow = presentation.rows.find((row) =>
    /amount|total|bill/i.test(row.label),
  ) ?? presentation.rows[0];

  if (!amountRow) {
    return null;
  }

  const keys = presentation.columns.map((column) => column.key);
  const previousKey = keys.includes("previous")
    ? "previous"
    : keys[0];
  const currentKey = keys.includes("current")
    ? "current"
    : keys[1] ?? keys[0];

  const previousValue = amountRow.values[previousKey];
  const currentValue = amountRow.values[currentKey];
  const previousAmount = previousValue
    ? parseInr(previousValue)
    : null;
  const currentAmount = currentValue
    ? parseInr(currentValue)
    : null;

  if (
    previousAmount === null
    || currentAmount === null
    || previousAmount === 0
  ) {
    return null;
  }

  const delta = currentAmount - previousAmount;
  const pctRaw = (delta / previousAmount) * 100;
  const pctRounded = Math.round(pctRaw);
  const pctLabel =
    delta !== 0 && pctRounded === 0
      ? pctRaw.toFixed(1)
      : String(Math.abs(pctRounded));
  const direction = delta > 0 ? "↑" : delta < 0 ? "↓" : "→";
  const trendClass =
    delta > 0
      ? "text-[#9b3d35]"
      : delta < 0
        ? "text-[#3d8b66]"
        : "text-[#7d8b81]";

  return (
    <div className="mb-3 rounded-lg border border-[#dfe7e0] bg-[#f8faf8] px-4 py-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
        {amountRow.label}
      </p>
      <p className="mt-1 text-[18px] font-semibold tabular-nums text-[#1c342b]">
        {previousValue}
        <span className="mx-2 text-[#96a198]">→</span>
        {currentValue}
        <span className={["ml-2 text-[13px]", trendClass].join(" ")}>
          ({direction}
          {delta === 0 ? "0" : pctLabel}%)
        </span>
      </p>
    </div>
  );
}
