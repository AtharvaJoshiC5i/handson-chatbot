import type { PresentationMeta } from "../types/chat";

interface PresentationTrustStripProps {
  meta?: PresentationMeta | null;
}

export function PresentationTrustStrip({
  meta,
}: PresentationTrustStripProps) {
  if (!meta?.period_label && !meta?.scope_label) {
    return null;
  }

  const parts: string[] = [];

  if (meta.period_label) {
    parts.push(meta.period_label);
  }

  if (meta.scope_label) {
    parts.push(meta.scope_label);
  }

  return (
    <div
      className="mb-2.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] font-medium uppercase tracking-[0.06em] text-[#7d8b81]"
      aria-label="Answer scope"
    >
      <span className="inline-flex items-center gap-1.5 rounded-full border border-[#e3ebe4] bg-[#f7faf7] px-2.5 py-1 text-[#5a6d62]">
        <span
          className="size-1.5 rounded-full bg-[#5c9a73]"
          aria-hidden="true"
        />
        {parts.join(" · ")}
      </span>
    </div>
  );
}
