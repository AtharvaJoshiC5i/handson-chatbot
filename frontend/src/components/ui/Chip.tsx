import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

type ChipVariant = "default" | "attention" | "attentionHigh" | "prompt";

const VARIANT: Record<ChipVariant, string> = {
  default: cn(
    "border-line bg-surface text-ink",
    "hover:border-stone-300 hover:bg-canvas",
  ),
  attention: cn(
    "rounded-full border-line/80 bg-surface text-stone-600",
    "hover:border-brand/25 hover:shadow-sm",
  ),
  attentionHigh: cn(
    "rounded-full border-amber-200/80 bg-amber-50 text-amber-900",
    "hover:border-amber-300",
  ),
  prompt: cn(
    "border-line/90 bg-surface pl-1.5 pr-3.5 text-[11px] text-ink",
    "hover:border-brand/20 hover:shadow-sm shadow-stone-900/5",
  ),
};

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ChipVariant;
  children: ReactNode;
}

export function Chip({
  variant = "default",
  className,
  type = "button",
  children,
  ...props
}: ChipProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex max-w-full items-center gap-2 rounded-lg border",
        "px-3 py-2 text-left text-xs font-medium leading-snug",
        "transition-[color,background-color,border-color,box-shadow] duration-150",
        "motion-reduce:transition-none",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/30",
        "disabled:cursor-not-allowed disabled:opacity-45",
        VARIANT[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
