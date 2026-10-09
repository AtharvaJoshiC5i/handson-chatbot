import { Database, MessagesSquare } from "lucide-react";

import { cn } from "../../lib/cn";

import type { AppPage } from "./AppSidebar";

interface MobileTabBarProps {
  appPage: AppPage;
  onPageChange: (page: AppPage) => void;
}

const TABS: {
  page: AppPage;
  label: string;
  icon: typeof MessagesSquare;
}[] = [
  { page: "support", label: "Support", icon: MessagesSquare },
  { page: "database", label: "Data", icon: Database },
];

export function MobileTabBar({ appPage, onPageChange }: MobileTabBarProps) {
  return (
    <nav
      className={[
        "flex shrink-0 gap-1 border-t border-line bg-surface/90 px-2 py-1.5 backdrop-blur-md lg:hidden",
      ].join(" ")}
      aria-label="Mobile navigation"
    >
      {TABS.map(({ page, label, icon: Icon }) => {
        const active = appPage === page;

        return (
          <button
            key={page}
            type="button"
            onClick={() => onPageChange(page)}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 rounded-lg py-2",
              "text-[10px] font-semibold transition-colors duration-150",
              active
                ? "bg-canvas text-brand shadow-sm ring-1 ring-line"
                : "text-muted hover:text-ink",
            )}
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </button>
        );
      })}
    </nav>
  );
}
