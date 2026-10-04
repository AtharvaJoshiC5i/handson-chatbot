import type { TablePresentation } from "../types/chat";

import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface BillListCardsProps {
  presentation: TablePresentation;
  onEntitySelect?: (message: string) => void;
}

export function isBillTablePresentation(
  presentation: TablePresentation,
): boolean {
  const title = presentation.title?.toLowerCase() ?? "";

  if (!title.includes("bill")) {
    return false;
  }

  return presentation.columns.some((column) =>
    /bill/i.test(column.key),
  );
}

export function BillListCards({
  presentation,
  onEntitySelect,
}: BillListCardsProps) {
  if (!isBillTablePresentation(presentation)) {
    return null;
  }

  const billIdKey = presentation.columns.find((column) =>
    /bill/i.test(column.key),
  )?.key!;

  return (
    <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
      {presentation.rows.map((row, index) => {
        const billId = row[billIdKey];
        const status = row.status ?? row.payment_status ?? "";
        const variant = statusVariantForValue(status);
        const amount = row.amount ?? row.total ?? "—";
        const period = row.period ?? row.billing_period ?? row.due_date ?? "";

        return (
          <article
            key={`${billId}-${index}`}
            className="min-w-[200px] shrink-0 rounded-lg border border-[#dfe7e0] bg-white p-3 shadow-sm"
          >
            <button
              type="button"
              className="text-left"
              onClick={() => onEntitySelect?.(`Tell me about ${billId}`)}
            >
              <p className="text-[11px] font-semibold text-[#28624c]">
                {billId}
              </p>
            </button>
            <p className="mt-2 text-[16px] font-semibold tabular-nums text-[#1c342b]">
              {amount}
            </p>
            <p className="mt-1 text-[10px] text-[#7d8b81]">{period}</p>
            {variant && status && (
              <div className="mt-2">
                <StatusChip label={status} variant={variant} />
              </div>
            )}
            {row.plan_type && (
              <p className="mt-2 text-[9px] font-semibold uppercase text-[#96a198]">
                {row.plan_type}
              </p>
            )}
          </article>
        );
      })}
    </div>
  );
}
