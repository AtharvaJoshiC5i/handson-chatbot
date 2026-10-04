import type { ListPresentation } from "../types/chat";

import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface PaymentRowListProps {
  presentation: ListPresentation;
}

export function isPaymentListPresentation(
  presentation: ListPresentation,
): boolean {
  const title = presentation.title?.toLowerCase() ?? "";

  return title.includes("payment");
}

export function PaymentRowList({
  presentation,
}: PaymentRowListProps) {
  if (!isPaymentListPresentation(presentation)) {
    return null;
  }

  return (
    <div className="space-y-2">
      {presentation.items.map((item, index) => {
        const variant = statusVariantForValue(item.value);

        return (
          <div
            key={`${item.label}-${index}`}
            className="flex items-start gap-3 rounded-lg border border-[#edf1ed] bg-[#fcfdfb] px-3 py-2.5"
          >
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-medium text-[#2c4135]">
                {item.label}
              </p>
              {item.detail && (
                <p className="mt-0.5 text-[10px] text-[#9b3d35]">
                  {item.detail}
                </p>
              )}
            </div>
            {variant ? (
              <StatusChip label={item.value} variant={variant} />
            ) : (
              <span className="text-[11px] font-semibold tabular-nums text-[#52665a]">
                {item.value}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
