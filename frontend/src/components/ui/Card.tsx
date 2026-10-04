import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: "none" | "sm" | "md";
}

const PADDING = {
  none: "",
  sm: "p-3",
  md: "p-4 sm:p-5",
};

export function Card({
  children,
  padding = "md",
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-surface ring-1 ring-line/80 shadow-sm shadow-stone-900/5",
        PADDING[padding],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Section({
  title,
  children,
  className,
  ...props
}: SectionProps) {
  return (
    <section className={cn("space-y-3", className)} {...props}>
      {title ? (
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
          {title}
        </h2>
      ) : null}
      {children}
    </section>
  );
}
