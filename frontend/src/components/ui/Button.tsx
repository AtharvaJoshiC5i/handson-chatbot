import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "outline" | "ghost";
type ButtonSize = "sm" | "md" | "icon";

const VARIANT: Record<ButtonVariant, string> = {
  primary: cn(
    "bg-brand text-white shadow-sm shadow-stone-900/5",
    "hover:bg-brand-hover",
    "focus-visible:ring-brand/35",
  ),
  outline: cn(
    "border border-line bg-surface text-ink",
    "hover:bg-canvas",
    "focus-visible:ring-brand/35",
  ),
  ghost: cn(
    "text-muted hover:bg-stone-100 hover:text-ink",
    "focus-visible:ring-brand/35",
  ),
};

const SIZE: Record<ButtonSize, string> = {
  sm: "h-8 gap-1.5 px-3 text-xs font-medium",
  md: "h-9 gap-2 px-3.5 text-xs font-medium",
  icon: "size-9 shrink-0 p-0",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  type = "button",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-lg",
        "transition-colors duration-150 motion-reduce:transition-none",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-canvas",
        "disabled:pointer-events-none disabled:opacity-40",
        VARIANT[variant],
        SIZE[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  label: string;
  children: ReactNode;
}

export function IconButton({
  active = false,
  label,
  className,
  children,
  ...props
}: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      className={cn(
        "inline-flex size-9 shrink-0 items-center justify-center rounded-lg",
        "transition-colors duration-150 motion-reduce:transition-none",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/35 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-40",
        active
          ? "bg-brand text-white shadow-sm hover:bg-brand-hover"
          : "bg-stone-100 text-muted hover:bg-stone-200 hover:text-ink",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
