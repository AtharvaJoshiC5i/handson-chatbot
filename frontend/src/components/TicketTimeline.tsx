import type { ListPresentation } from "../types/chat";

import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface TicketTimelineProps {
  presentation: ListPresentation;
}

export function isTicketTimelinePresentation(
  presentation: ListPresentation,
): boolean {
  const title = presentation.title?.toLowerCase() ?? "";

  return title.includes("update") || title.includes("timeline");
}

export function TicketTimeline({
  presentation,
}: TicketTimelineProps) {
  if (!isTicketTimelinePresentation(presentation)) {
    return null;
  }

  return (
    <ol className="relative ml-2 space-y-0 border-l border-[#dce6de] pl-5">
      {presentation.items.map((item, index) => {
        const variant = statusVariantForValue(item.value);

        return (
          <li
            key={`${item.label}-${index}`}
            className="relative pb-4 last:pb-0"
          >
            <span
              className="absolute -left-[1.35rem] top-1.5 size-2.5 rounded-full bg-[#3d8b66] ring-4 ring-white"
              aria-hidden="true"
            />
            <p className="text-[10px] font-medium text-[#96a198]">
              {item.label}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              {variant ? (
                <StatusChip label={item.value} variant={variant} />
              ) : (
                <span className="text-[12px] font-semibold text-[#2c4135]">
                  {item.value}
                </span>
              )}
            </div>
            {item.detail && (
              <p className="mt-1 text-[11px] leading-5 text-[#7d8b81]">
                {item.detail}
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
