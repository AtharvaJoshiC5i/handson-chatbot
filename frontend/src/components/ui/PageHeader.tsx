import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex h-14 shrink-0 items-center justify-between",
        "border-b border-line bg-surface/90 px-4 backdrop-blur-md sm:px-6",
        className,
      )}
    >
      <div className="min-w-0">
        <p className="truncate text-[13px] font-semibold tracking-tight text-ink">
          {title}
        </p>
        {subtitle ? (
          <p className="truncate text-[11px] text-muted">{subtitle}</p>
        ) : null}
      </div>
      {actions ? <div className="shrink-0">{actions}</div> : null}
    </header>
  );
}
