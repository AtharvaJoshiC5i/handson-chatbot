import type { AccountSnapshot } from "../../types/account";
import { UsageMeter } from "../UsageMeter";
import { formatInr, lineLabel } from "../../utils/accountFormat";
import {
  billStatusTone,
  formatDisplayDate,
  parseUsageHeadline,
  subscriptionMonthlyPrice,
} from "../../utils/welcomePersonalization";
import { BillsByLineTiles } from "./BillsByLineTiles";

interface WelcomePersonalSummaryProps {
  snapshot: AccountSnapshot;
  firstName: string;
}

function planFootnote(snapshot: AccountSnapshot): string {
  const parts: string[] = [];
  const renewal = formatDisplayDate(snapshot.plan?.renewal_date);

  if (renewal) {
    parts.push(`Renews ${renewal}`);
  }

  if (snapshot.payment_profile?.autopay_enabled) {
    parts.push("Autopay on");
  } else if (snapshot.has_payment_profile) {
    parts.push("Autopay off");
  }

  if (snapshot.payment_profile?.payment_method_label) {
    parts.push(snapshot.payment_profile.payment_method_label);
  }

  if (snapshot.available_credits > 0) {
    parts.push(`${formatInr(snapshot.available_credits)} credits`);
  }

  return parts.join(" · ");
}

export function WelcomePersonalSummary({
  snapshot,
  firstName,
}: WelcomePersonalSummaryProps) {
  const parsedUsage = parseUsageHeadline(
    snapshot.usage_headline,
    snapshot.plan,
  );
  const monthlyPrice = subscriptionMonthlyPrice(snapshot);
  const footnote = planFootnote(snapshot);

  return (
    <article
      className="welcome-personal-card"
      aria-label={`${firstName}'s account`}
    >
      <div className="welcome-personal-card-body">
        <section>
          <p className="welcome-section-kicker">Your plan</p>
          <p className="welcome-plan-name welcome-plan-name--minimal">
            {snapshot.plan?.plan_name ?? "—"}
          </p>
          <p className="welcome-plan-meta">
            {snapshot.plan?.plan_type
              ? `${lineLabel(snapshot.plan.plan_type)}`
              : "Line"}
            {monthlyPrice !== null ? ` · ${formatInr(monthlyPrice)}/mo` : ""}
          </p>
          {footnote && (
            <p className="welcome-personal-footnote">{footnote}</p>
          )}
        </section>

        <section>
          {parsedUsage ? (
            <UsageMeter
              usedGb={parsedUsage.usedGb}
              limitGb={
                parsedUsage.limitGb || snapshot.plan?.data_limit_gb || 0
              }
              isUnlimited={parsedUsage.isUnlimited}
              label={`${firstName}'s data · this month`}
              compact
            />
          ) : (
            <>
              <p className="welcome-section-kicker">Usage</p>
              <p className="text-[13px] font-medium text-[var(--color-ink)]">
                {snapshot.usage_headline ?? "—"}
              </p>
            </>
          )}
          {snapshot.payment?.status === "FAILED" && (
            <p className="welcome-personal-alert">
              Latest payment failed
              {snapshot.payment.failure_reason
                ? ` — ${snapshot.payment.failure_reason}`
                : ""}
            </p>
          )}
        </section>
      </div>

      {snapshot.bill && (
        <div className="welcome-personal-bill">
          <div className="flex items-baseline justify-between gap-2">
            <div>
              <p className="welcome-section-kicker">
                Latest bill · {snapshot.bill.bill_id}
              </p>
              <p className="welcome-bill-amount welcome-bill-amount--minimal">
                {formatInr(snapshot.bill.amount)}
              </p>
            </div>
            <span
              className="welcome-bill-chip"
              data-tone={billStatusTone(snapshot.bill.status)}
            >
              {snapshot.bill.status.replace(/_/g, " ")}
            </span>
          </div>
          <p className="welcome-bill-detail">
            {lineLabel(snapshot.bill.plan_type)} · Due{" "}
            {formatDisplayDate(snapshot.bill.due_date) ?? "—"}
            {snapshot.projected_bill && (
              <>
                {" "}
                · Est. {formatInr(snapshot.projected_bill.estimated_amount)}
              </>
            )}
          </p>
        </div>
      )}

      {snapshot.bills_by_line.length > 1 && (
        <div className="welcome-personal-bill border-t-0 pt-0">
          <BillsByLineTiles snapshot={snapshot} variant="embedded" />
        </div>
      )}
    </article>
  );
}
