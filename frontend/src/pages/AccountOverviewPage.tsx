import type { AccountSnapshot } from "../types/account";
import { AccountAttentionList } from "../components/account/AccountAttentionList";
import { AccountSubscriptionsList } from "../components/account/AccountSubscriptionsList";
import { WelcomePersonalHero } from "../components/account/WelcomePersonalHero";
import { WelcomePersonalSummary } from "../components/account/WelcomePersonalSummary";
import { formatVerifiedAt } from "../utils/accountFormat";

interface AccountOverviewPageProps {
  displayName: string;
  snapshot: AccountSnapshot | null;
  loading?: boolean;
  onAskInChat: (message: string) => void;
  disabled?: boolean;
}

export function AccountOverviewPage({
  displayName,
  snapshot,
  loading = false,
  onAskInChat,
  disabled = false,
}: AccountOverviewPageProps) {
  const firstName = displayName.split(" ")[0];

  if (loading) {
    return (
      <div className="account-overview-scroll">
        <div className="account-overview-inner account-overview-inner--minimal">
          <div
            className="welcome-skeleton min-h-[12rem]"
            aria-hidden="true"
          />
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className="account-overview-scroll">
        <div className="account-overview-inner account-overview-inner--minimal">
          <p className="text-[13px] text-[var(--color-muted)]">
            No account data is available for this customer.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="account-overview-scroll">
      <div className="account-overview-inner account-overview-inner--minimal">
        <WelcomePersonalHero
          displayName={displayName}
          snapshot={snapshot}
          useTimeGreeting={false}
        />

        <WelcomePersonalSummary
          snapshot={snapshot}
          firstName={firstName}
        />

        {snapshot.active_subscriptions.length > 1 && (
          <AccountSubscriptionsList snapshot={snapshot} />
        )}

        <AccountAttentionList
          snapshot={snapshot}
          disabled={disabled}
          onAskInChat={onAskInChat}
          variant="minimal"
        />

        <footer className="account-overview-footer account-overview-footer--minimal">
          <p>
            As of {formatVerifiedAt(snapshot.generated_at)} · same records as
            chat
          </p>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onAskInChat("Give me an overview of my account")}
            className="welcome-prompt-chip welcome-prompt-chip--minimal mt-3"
          >
            Ask in chat
          </button>
        </footer>
      </div>
    </div>
  );
}
