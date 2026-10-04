import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

interface NavItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  children: ReactNode;
}

export function NavItem({
  active = false,
  className,
  type = "button",
  children,
  ...props
}: NavItemProps) {
  return (
    <button
      type={type}
      className={cn(
        "flex h-10 w-full items-center gap-2.5 rounded-lg px-3",
        "text-[13px] font-medium text-stone-600",
        "transition-colors duration-150 motion-reduce:transition-none",
        "hover:bg-stone-100 hover:text-brand",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/30",
        "disabled:opacity-40",
        active && "border-l-2 border-brand bg-stone-50 pl-[10px] font-semibold text-brand",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
