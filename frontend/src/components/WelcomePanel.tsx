import { useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";

import type { AccountSnapshot } from "../types/account";
import { formatInr } from "../utils/accountFormat";
import {
  QUICK_QUESTIONS_ANALYTICS,
  QUICK_QUESTIONS_TO_GET_STARTED,
} from "../utils/quickQuestions";
import { prioritizeQuickQuestions } from "../utils/welcomePersonalization";
import { WelcomeAttentionCard } from "./WelcomeAttentionCard";

interface WelcomePanelProps {
  name: string;
  snapshot: AccountSnapshot | null;
  loading?: boolean;
  onPrompt: (message: string) => void;
  disabled?: boolean;
}

export function WelcomePanel({
  name,
  snapshot,
  loading = false,
  onPrompt,
  disabled = false,
}: WelcomePanelProps) {
  const [showMorePrompts, setShowMorePrompts] = useState(false);

  const firstName = name.split(" ")[0];

  const attentionItems = snapshot?.attention_items ?? [];
  const manyAlerts = attentionItems.length >= 3;

  const basePrompts = showMorePrompts
    ? [...QUICK_QUESTIONS_TO_GET_STARTED, ...QUICK_QUESTIONS_ANALYTICS]
    : QUICK_QUESTIONS_TO_GET_STARTED;

  const visiblePrompts = useMemo(() => {
    if (!snapshot) {
      return basePrompts;
    }

    return prioritizeQuickQuestions(basePrompts, snapshot);
  }, [basePrompts, snapshot]);

  return (
    <div
      className={[
        "welcome-panel flex min-h-0 flex-1 flex-col items-center px-5 py-6 sm:px-6",
        manyAlerts
          ? "justify-start overflow-y-auto sm:py-8"
          : "justify-center",
      ].join(" ")}
    >
      <div className="welcome-landing w-full max-w-[600px]">
        <header className="text-center">
          <h1 className="welcome-heading text-[26px] font-semibold tracking-tight text-[var(--color-brand)] sm:text-[30px]">
            Hi, {firstName}
          </h1>
          <span className="welcome-heading-accent" aria-hidden="true" />
          <p className="welcome-description mx-auto mt-3 max-w-md text-[13px] leading-relaxed text-[var(--color-muted)]">
            Structured answers from your account — plan, usage, bills, and
            payments.
          </p>
        </header>

        {loading ? (
          <div
            className="welcome-skeleton welcome-snapshot-premium mx-auto mt-8 max-w-md min-h-[5.5rem]"
            aria-hidden="true"
          />
        ) : snapshot ? (
          <>
            <section
              className="welcome-glance-wrap welcome-snapshot-premium mx-auto mt-8 max-w-md sm:max-w-lg"
              aria-label="Account at a glance"
            >
              <div className="welcome-snapshot welcome-snapshot--in-glance">
                <div className="welcome-snapshot-grid">
                  <div className="welcome-stat-cell">
                    <p className="welcome-stat-label">Plan</p>
                    <p className="welcome-stat-value">
                      {snapshot.plan?.plan_name ?? "—"}
                    </p>
                  </div>
                  <div className="welcome-stat-cell">
                    <p className="welcome-stat-label">Usage</p>
                    <p className="welcome-stat-value">
                      {snapshot.usage_headline ?? "—"}
                    </p>
                  </div>
                  <div className="welcome-stat-cell">
                    <p className="welcome-stat-label">Bill</p>
                    <p className="welcome-stat-value">
                      {snapshot.bill
                        ? formatInr(snapshot.bill.amount)
                        : "—"}
                    </p>
                  </div>
                </div>

                {snapshot.projected_bill && (
                  <p className="welcome-snapshot-foot">
                    Est. this month:{" "}
                    <strong>
                      {formatInr(snapshot.projected_bill.estimated_amount)}
                    </strong>
                  </p>
                )}
              </div>

              {!loading && attentionItems.length > 0 && (
                <WelcomeAttentionCard
                  items={attentionItems}
                  disabled={disabled}
                  onPrompt={onPrompt}
                />
              )}
            </section>
          </>
        ) : null}

        <div
          className={[
            "welcome-topics welcome-topics--landing",
            manyAlerts ? "welcome-topics--compact" : "",
          ].join(" ")}
        >
          <p className="welcome-section-label">Quick questions</p>

          <div
            className="welcome-topic-grid mt-3.5 flex flex-wrap justify-center gap-2"
            aria-label="Quick questions"
          >
            {visiblePrompts.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.message}
                  type="button"
                  disabled={disabled}
                  onClick={() => onPrompt(item.message)}
                  className="welcome-prompt-chip welcome-prompt-chip--premium"
                >
                  <span className="welcome-prompt-icon">
                    <Icon size={13} strokeWidth={1.85} aria-hidden="true" />
                  </span>
                  {item.label}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            disabled={disabled}
            onClick={() => setShowMorePrompts((open) => !open)}
            className="welcome-more-toggle welcome-more-toggle--landing focus-visible:outline-none focus-visible:underline"
          >
            {showMorePrompts ? "Fewer suggestions" : "More insights"}
            <ChevronDown
              size={14}
              className={[
                "transition-transform duration-200",
                showMorePrompts ? "rotate-180" : "",
              ].join(" ")}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>
    </div>
  );
}
