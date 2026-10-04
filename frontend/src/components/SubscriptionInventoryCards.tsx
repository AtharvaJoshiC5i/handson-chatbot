import type { ListPresentation } from "../types/chat";

import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface SubscriptionInventoryCardsProps {
  presentation: ListPresentation;
}

export function isSubscriptionListPresentation(
  presentation: ListPresentation,
): boolean {
  const title = presentation.title?.toLowerCase() ?? "";

  return title.includes("subscription");
}

export function SubscriptionInventoryCards({
  presentation,
}: SubscriptionInventoryCardsProps) {
  if (!isSubscriptionListPresentation(presentation)) {
    return null;
  }

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {presentation.items.map((item, index) => {
        const variant = statusVariantForValue(item.value);

        return (
          <article
            key={`${item.label}-${index}`}
            className="rounded-lg border border-[#dfe7e0] bg-white p-3"
          >
            <p className="text-[12px] font-semibold text-[#2c4135]">
              {item.label}
            </p>
            <div className="mt-2 flex items-center justify-between gap-2">
              {variant ? (
                <StatusChip label={item.value} variant={variant} />
              ) : (
                <span className="text-[11px] font-medium text-[#52665a]">
                  {item.value}
                </span>
              )}
            </div>
            {item.detail && (
              <p className="mt-2 text-[10px] text-[#7d8b81]">
                {item.detail}
              </p>
            )}
          </article>
        );
      })}
    </div>
  );
}
