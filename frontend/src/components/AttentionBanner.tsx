import { CircleAlert, X } from "lucide-react";
import { useState } from "react";

import type { SnapshotAttentionItem } from "../types/account";

interface AttentionBannerProps {
  items: SnapshotAttentionItem[];
}

export function AttentionBanner({
  items,
}: AttentionBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed || items.length === 0) {
    return null;
  }

  const primary = items.find(
    (item) => item.severity === "high",
  ) ?? items[0];

  return (
    <div
      role="status"
      className="mb-4 flex items-start gap-3 rounded-lg border border-[#ead9b8] bg-[#faf6ee] px-3.5 py-3 text-[11px] leading-5 text-[#6f4f1a]"
    >
      <CircleAlert
        size={16}
        className="mt-0.5 shrink-0"
        aria-hidden="true"
      />

      <div className="min-w-0 flex-1">
        <p className="font-semibold text-[#5a4015]">
          {primary.domain} needs attention
        </p>
        <p className="mt-0.5">{primary.message}</p>
        {items.length > 1 && (
          <p className="mt-1 text-[10px] text-[#8a7345]">
            +{items.length - 1} more alert
            {items.length - 1 === 1 ? "" : "s"}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="shrink-0 rounded-md p-1 text-[#8a7345] hover:bg-[#f0e6d4]"
        aria-label="Dismiss alert"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </div>
  );
}
