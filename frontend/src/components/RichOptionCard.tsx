import type { LucideIcon } from "lucide-react";
import {
  ArrowUpRight,
  ChartNoAxesColumnIncreasing,
  CircleHelp,
  CreditCard,
  Headphones,
  ReceiptText,
  Wallet,
} from "lucide-react";

import type { ChatOption } from "../types/chat";

function iconForOption(option: ChatOption): LucideIcon {
  const text = `${option.label} ${option.message}`.toLowerCase();

  if (text.includes("bill")) {
    return ReceiptText;
  }

  if (text.includes("payment") || text.includes("pay")) {
    return Wallet;
  }

  if (text.includes("usage") || text.includes("data")) {
    return ChartNoAxesColumnIncreasing;
  }

  if (text.includes("plan")) {
    return CreditCard;
  }

  if (text.includes("ticket") || text.includes("support")) {
    return Headphones;
  }

  return CircleHelp;
}

interface RichOptionCardProps {
  option: ChatOption;
  disabled?: boolean;
  onSelect: (message: string) => void;
}

export function RichOptionCard({
  option,
  disabled = false,
  onSelect,
}: RichOptionCardProps) {
  const Icon = iconForOption(option);

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onSelect(option.message)}
      className={[
        "group flex min-w-[140px] max-w-[220px] flex-1 flex-col rounded-lg border border-[#dce6de]",
        "bg-white px-3 py-2.5 text-left transition",
        "hover:border-[#aec4b3] hover:bg-[#f5f8f5]",
        "disabled:opacity-40",
      ].join(" ")}
    >
      <span className="flex items-center gap-2">
        <span className="grid size-7 place-items-center rounded-md bg-[#edf3ef] text-[#3d6b55]">
          <Icon size={14} strokeWidth={1.8} aria-hidden="true" />
        </span>
        <span className="text-[11px] font-semibold text-[#2c4135]">
          {option.label}
        </span>
        <ArrowUpRight
          size={12}
          className="ml-auto text-[#9aa69e] group-hover:text-[#345342]"
          aria-hidden="true"
        />
      </span>
      <span className="mt-1 line-clamp-2 text-[10px] leading-4 text-[#819087]">
        {option.message}
      </span>
    </button>
  );
}
