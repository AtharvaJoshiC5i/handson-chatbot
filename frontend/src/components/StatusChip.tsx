import type { StatusVariant } from "../utils/statusChip";

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  success: "bg-[#e6f2ea] text-[#256647] ring-[#c5dfd0]",
  warning: "bg-[#faf3e6] text-[#8a5c1a] ring-[#ead9b8]",
  danger: "bg-[#fcecea] text-[#9b3d35] ring-[#f0cbc7]",
  info: "bg-[#e8f0f6] text-[#35607d] ring-[#c8dbe8]",
  neutral: "bg-[#eef1ef] text-[#5a6b61] ring-[#d8e0da]",
};

interface StatusChipProps {
  label: string;
  variant: StatusVariant;
}

export function StatusChip({
  label,
  variant,
}: StatusChipProps) {
  return (
    <span
      className={[
        "inline-flex max-w-full items-center rounded-full px-2 py-0.5",
        "text-[10px] font-semibold uppercase tracking-wide",
        "ring-1 ring-inset",
        VARIANT_CLASSES[variant],
      ].join(" ")}
    >
      <span className="truncate">{label}</span>
    </span>
  );
}
