import type { AccountSnapshot } from "../types/account";
import { formatInr } from "../utils/accountFormat";

interface ChatAccountGlanceProps {
  snapshot: AccountSnapshot;
}

export function ChatAccountGlance({
  snapshot,
}: ChatAccountGlanceProps) {
  return (
    <div
      className="chat-account-glance"
      aria-label="Account at a glance"
    >
      <div className="chat-account-glance-grid">
        <div className="chat-account-glance-cell">
          <span className="chat-account-glance-label">Plan</span>
          <span className="chat-account-glance-value">
            {snapshot.plan?.plan_name ?? "—"}
          </span>
        </div>
        <div className="chat-account-glance-cell">
          <span className="chat-account-glance-label">Usage</span>
          <span className="chat-account-glance-value">
            {snapshot.usage_headline ?? "—"}
          </span>
        </div>
        <div className="chat-account-glance-cell">
          <span className="chat-account-glance-label">Bill</span>
          <span className="chat-account-glance-value">
            {snapshot.bill
              ? formatInr(snapshot.bill.amount)
              : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
