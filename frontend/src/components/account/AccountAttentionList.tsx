import type { AccountSnapshot } from "../../types/account";

interface AccountAttentionListProps {
  snapshot: AccountSnapshot;
  disabled?: boolean;
  onAskInChat?: (message: string) => void;
  variant?: "default" | "minimal";
}

export function AccountAttentionList({
  snapshot,
  disabled = false,
  onAskInChat,
  variant = "default",
}: AccountAttentionListProps) {
  const attentionItems = snapshot.attention_items;

  if (attentionItems.length === 0) {
    return null;
  }

  if (variant === "minimal") {
    return (
      <section
        className="account-overview-section account-overview-section--minimal"
        aria-label="Items needing attention"
      >
        <h2 className="account-overview-section-title">For you</h2>
        <ul className="space-y-2">
          {attentionItems.map((item) => (
            <li key={`${item.domain}-${item.message}`}>
              {item.prompt && onAskInChat ? (
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onAskInChat(item.prompt!)}
                  className="welcome-personal-attention w-full text-left"
                >
                  <span className="font-medium text-[#456350]">
                    {item.domain}
                  </span>
                  <span className="text-[#6d7f73]"> — {item.message}</span>
                </button>
              ) : (
                <p className="welcome-personal-footnote py-1">
                  <span className="font-medium">{item.domain}</span>
                  {" — "}
                  {item.message}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>
    );
  }

  return (
    <section
      className="account-overview-section"
      aria-label="Items needing attention"
    >
      <h2 className="account-overview-section-title">Needs attention</h2>

      <ul className="space-y-2">
        {attentionItems.map((item) => (
          <li
            key={`${item.domain}-${item.message}`}
            className="account-overview-attention-row"
          >
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-[#8a968d]">
                {item.domain}
              </p>
              <p className="mt-0.5 text-[12px] leading-snug text-[#345342]">
                {item.message}
              </p>
            </div>
            {item.prompt && onAskInChat && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => onAskInChat(item.prompt!)}
                className="account-overview-ask-btn shrink-0"
              >
                Ask in chat
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
