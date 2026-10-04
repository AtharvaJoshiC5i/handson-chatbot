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

  const [leftKey, rightKey] = presentation.columns.map(
    (column) => column.key,
  );
  const leftValue = amountRow.values[leftKey];
  const rightValue = amountRow.values[rightKey];
  const leftAmount = leftValue ? parseInr(leftValue) : null;
  const rightAmount = rightValue ? parseInr(rightValue) : null;

  if (leftAmount === null || rightAmount === null || leftAmount === 0) {
    return null;
  }

  const delta = rightAmount - leftAmount;
  const pct = Math.round((delta / leftAmount) * 100);
  const direction = delta >= 0 ? "↑" : "↓";

  return (
    <div className="mb-3 rounded-lg border border-[#dfe7e0] bg-[#f8faf8] px-4 py-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
        {amountRow.label}
      </p>
      <p className="mt-1 text-[18px] font-semibold tabular-nums text-[#1c342b]">
        {leftValue}
        <span className="mx-2 text-[#96a198]">→</span>
        {rightValue}
        <span
          className={[
            "ml-2 text-[13px]",
            delta >= 0 ? "text-[#9b3d35]" : "text-[#3d8b66]",
          ].join(" ")}
        >
          ({direction}
          {Math.abs(pct)}%)
        </span>
      </p>
    </div>
  );
}
