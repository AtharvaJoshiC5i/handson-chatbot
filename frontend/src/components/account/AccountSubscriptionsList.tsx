import type { AccountSnapshot } from "../../types/account";
import { formatDisplayDate } from "../../utils/welcomePersonalization";
import { formatInr, lineLabel } from "../../utils/accountFormat";

interface AccountSubscriptionsListProps {
  snapshot: AccountSnapshot;
}

export function AccountSubscriptionsList({
  snapshot,
}: AccountSubscriptionsListProps) {
  const subscriptions = snapshot.active_subscriptions;

  if (subscriptions.length === 0) {
    return null;
  }

  return (
    <section
      className="account-overview-section account-overview-section--minimal"
      aria-label="Active subscriptions"
    >
      <h2 className="account-overview-section-title">
        Active subscriptions
      </h2>
      <ul className="account-overview-list">
        {subscriptions.map((sub) => (
          <li key={sub.subscription_id} className="account-overview-list-item">
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-[var(--color-ink)]">
                {sub.plan_name}
              </p>
              <p className="mt-0.5 text-[11px] text-[#6d7f73]">
                {lineLabel(sub.plan_type)} · {sub.status.replace(/_/g, " ")}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[12px] font-semibold tabular-nums">
                {formatInr(sub.monthly_price)}
                <span className="text-[10px] font-medium text-[#8a968d]">
                  /mo
                </span>
              </p>
              <p className="mt-0.5 text-[10px] text-[#8a968d]">
                Renews {formatDisplayDate(sub.renewal_date) ?? "—"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
