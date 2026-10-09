import {
  Database,
  MessagesSquare,
  Plus,
  Signal,
  UserRound,
} from "lucide-react";

import { Button } from "../ui/Button";
import { NavItem } from "../ui/NavItem";

export type AppPage = "support" | "database";

interface AppSidebarProps {
  appPage: AppPage;
  displayName: string;
  loading: boolean;
  onPageChange: (page: AppPage) => void;
  onNewConversation: () => void;
}

export function AppSidebar({
  appPage,
  displayName,
  loading,
  onPageChange,
  onNewConversation,
}: AppSidebarProps) {
  return (
    <aside
      className={[
        "hidden w-60 shrink-0 flex-col border-r border-line bg-surface lg:flex",
      ].join(" ")}
    >
      <div className="flex h-16 items-center gap-3 border-b border-line px-4">
        <span
          className={[
            "grid size-9 place-items-center rounded-xl bg-canvas text-brand",
            "ring-1 ring-line shadow-sm",
          ].join(" ")}
        >
          <Signal size={17} strokeWidth={2} aria-hidden="true" />
        </span>
        <div>
          <span className="block text-[15px] font-semibold tracking-tight text-brand">
            NexaTel
          </span>
          <span className="mt-0.5 block text-[10px] text-muted">
            Self-care demo
          </span>
        </div>
      </div>

      {appPage === "support" && (
        <div className="px-3 pt-4">
          <Button
            size="md"
            className="w-full"
            onClick={onNewConversation}
            disabled={loading}
          >
            <Plus size={14} strokeWidth={2} aria-hidden="true" />
            New chat
          </Button>
        </div>
      )}

      <nav className="space-y-0.5 px-3 pt-4" aria-label="Workspace">
        <p className="px-3 pb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted">
          Workspace
        </p>
        <NavItem
          active={appPage === "support"}
          onClick={() => onPageChange("support")}
        >
          <MessagesSquare size={15} strokeWidth={1.8} aria-hidden="true" />
          Support
        </NavItem>
        <NavItem
          active={appPage === "database"}
          onClick={() => onPageChange("database")}
        >
          <Database size={15} strokeWidth={1.8} aria-hidden="true" />
          Database
        </NavItem>
      </nav>

      <div className="mt-auto border-t border-line px-4 py-4">
        <div className="flex items-center gap-3 px-2 py-1.5">
          <span
            className={[
              "grid size-8 shrink-0 place-items-center rounded-lg bg-canvas",
              "text-brand ring-1 ring-line",
            ].join(" ")}
          >
            <UserRound size={16} strokeWidth={1.8} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <span className="block text-[10px] text-muted">Demo account</span>
            <span className="mt-0.5 block truncate text-[11px] font-semibold text-ink">
              {displayName}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
