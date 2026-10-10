import { useMemo, useState } from "react";
import {
  Bell,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  CreditCard,
  Headphones,
  Signal,
  Sparkles,
} from "lucide-react";

import type { SnapshotAttentionItem } from "../types/account";

const COLLAPSED_VISIBLE = 2;

interface WelcomeAttentionCardProps {
  items: SnapshotAttentionItem[];
  disabled?: boolean;
  onPrompt: (message: string) => void;
}

function cleanAlertMessage(message: string): string {
  return message
    .replace(/^[\s⚠️🔔📵]+/u, "")
    .replace(/\s+/g, " ")
    .trim();
}

function severityRank(severity: string): number {
  return severity === "high" ? 0 : 1;
}

function domainIcon(domain: string) {
  const key = domain.toLowerCase();

  if (key.includes("bill") || key.includes("payment")) {
    return CreditCard;
  }

  if (key.includes("usage") || key.includes("plan")) {
    return Signal;
  }

  if (key.includes("support")) {
    return Headphones;
  }

  return Bell;
}

export function WelcomeAttentionCard({
  items,
  disabled = false,
  onPrompt,
}: WelcomeAttentionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const sortedItems = useMemo(
    () =>
      [...items].sort(
        (left, right) =>
          severityRank(left.severity) - severityRank(right.severity),
      ),
    [items],
  );

  if (sortedItems.length === 0) {
    return null;
  }

  const highCount = sortedItems.filter(
    (item) => item.severity === "high",
  ).length;
  const canCollapse = sortedItems.length > COLLAPSED_VISIBLE;
  const visibleItems = expanded || !canCollapse
    ? sortedItems
    : sortedItems.slice(0, COLLAPSED_VISIBLE);
  const hiddenCount = sortedItems.length - COLLAPSED_VISIBLE;

  return (
    <div className="welcome-glance-alerts" aria-label="Proactive account alerts">
      <div className="welcome-glance-alerts-head">
        <div className="welcome-glance-alerts-title-wrap">
          <Sparkles
            className="welcome-glance-alerts-spark"
            size={14}
            strokeWidth={2}
            aria-hidden
          />
          <div>
            <p className="welcome-glance-alerts-title">Needs your attention</p>
            <p className="welcome-glance-alerts-meta">
              {sortedItems.length} update
              {sortedItems.length === 1 ? "" : "s"}
              {highCount > 0
                ? ` · ${highCount} urgent`
                : ""}
            </p>
          </div>
        </div>
        {canCollapse && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => setExpanded((open) => !open)}
            className="welcome-glance-alerts-toggle"
            aria-expanded={expanded}
          >
            {expanded ? "Show less" : `+${hiddenCount} more`}
            <ChevronDown
              size={14}
              className={[
                "transition-transform duration-200",
                expanded ? "rotate-180" : "",
              ].join(" ")}
              aria-hidden
            />
          </button>
        )}
      </div>

      <ul
        className={[
          "welcome-glance-alerts-list",
          expanded && sortedItems.length > COLLAPSED_VISIBLE
            ? "welcome-glance-alerts-list--scrollable"
            : "",
        ].join(" ")}
      >
        {visibleItems.map((item) => {
          const Icon = domainIcon(item.domain);
          const isHigh = item.severity === "high";
          const message = cleanAlertMessage(item.message);

          return (
            <li key={`${item.domain}-${item.message}`}>
              <button
                type="button"
                disabled={disabled || !item.prompt}
                onClick={() => {
                  if (item.prompt) {
                    onPrompt(item.prompt);
                  }
                }}
                className={[
                  "welcome-glance-alert-row",
                  isHigh ? "welcome-glance-alert-row--high" : "",
                ].join(" ")}
              >
                <span
                  className={[
                    "welcome-glance-alert-icon",
                    isHigh ? "welcome-glance-alert-icon--high" : "",
                  ].join(" ")}
                  aria-hidden
                >
                  <Icon size={14} strokeWidth={2} />
                </span>

                <span className="welcome-glance-alert-copy">
                  <span className="welcome-glance-alert-domain">
                    {item.domain}
                  </span>
                  <span className="welcome-glance-alert-message">
                    {message}
                  </span>
                </span>

                {item.prompt ? (
                  <ChevronRight
                    className="welcome-glance-alert-chevron"
                    size={16}
                    aria-hidden
                  />
                ) : (
                  <CircleAlert
                    className="welcome-glance-alert-chevron opacity-40"
                    size={14}
                    aria-hidden
                  />
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
