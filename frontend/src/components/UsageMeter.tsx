interface UsageMeterProps {
  usedGb: number;
  limitGb: number;
  isUnlimited?: boolean;
  label?: string;
  className?: string;
  compact?: boolean;
}

export function UsageMeter({
  usedGb,
  limitGb,
  isUnlimited = false,
  label = "Data this month",
  className = "",
  compact = false,
}: UsageMeterProps) {
  const percentage = isUnlimited || limitGb <= 0
    ? 0
    : Math.min(100, Math.round((usedGb / limitGb) * 100));

  const barTone =
    percentage >= 100
      ? "bg-[#c45a4f]"
      : percentage >= 80
        ? "bg-[#c9923a]"
        : "bg-[#3d8b66]";

  return (
    <div
      className={[
        compact ? "p-0" : "rounded-lg border border-[#dfe7e0] bg-white p-4",
        className,
      ].join(" ")}
    >
      <div className="flex items-baseline justify-between gap-3">
        <p
          className={
            compact
              ? "text-[10px] font-semibold uppercase tracking-wide text-[#8a968d]"
              : "text-[11px] font-medium text-[#718076]"
          }
        >
          {label}
        </p>
        <p
          className={
            compact
              ? "text-[12px] font-semibold tabular-nums text-[var(--color-ink)]"
              : "text-[12px] font-semibold tabular-nums text-[#2c4135]"
          }
        >
          {isUnlimited
            ? `${usedGb.toFixed(1)} GB · Unlimited`
            : `${usedGb.toFixed(1)} / ${limitGb.toFixed(0)} GB`}
        </p>
      </div>

      {!isUnlimited && (
        <div
          className={`${compact ? "mt-2.5" : "mt-3"} h-1.5 overflow-hidden rounded-full bg-[#e8ede9] sm:h-2`}
          role="meter"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percentage}
          aria-label={`${label}: ${percentage}% used`}
        >
          <div
            className={`h-full rounded-full transition-all ${barTone}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
}
