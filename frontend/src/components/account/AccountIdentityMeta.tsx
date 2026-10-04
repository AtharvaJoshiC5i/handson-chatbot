import type { AccountSnapshot } from "../../types/account";
import {
  accountStatusLabel,
  accountStatusTone,
} from "../../utils/welcomePersonalization";

interface AccountIdentityMetaProps {
  snapshot: AccountSnapshot;
  className?: string;
}

export function AccountIdentityMeta({
  snapshot,
  className = "",
}: AccountIdentityMetaProps) {
  return (
    <div
      className={["welcome-meta", className].filter(Boolean).join(" ")}
      aria-label="Account identity"
    >
      <span>{snapshot.customer_id}</span>
      <span className="welcome-meta-dot" aria-hidden="true" />
      <span
        className="welcome-status-pill"
        data-tone={accountStatusTone(snapshot.account_status)}
      >
        {accountStatusLabel(snapshot.account_status)}
      </span>
      <span className="welcome-meta-dot" aria-hidden="true" />
      <span>{snapshot.city}</span>
      <span className="welcome-meta-dot" aria-hidden="true" />
      <span>{snapshot.phone_masked}</span>
    </div>
  );
}
