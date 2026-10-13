import { ArrowRight, Sparkles } from "lucide-react";

import type { SnapshotAttentionItem } from "../types/account";

interface WelcomeNextBestCardProps {
  item: SnapshotAttentionItem;
  disabled?: boolean;
  onPrompt: (message: string) => void;
}

function cleanMessage(message: string): string {
  return message
    .replace(/^[\s⚠️🔔📵]+/u, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function WelcomeNextBestCard({
  item,
  disabled = false,
  onPrompt,
}: WelcomeNextBestCardProps) {
  const prompt = item.prompt?.trim();

  if (!prompt) {
    return null;
  }

  const isUrgent = item.severity === "high";

  return (
    <div className="welcome-next-best" aria-label="Suggested next step">
      <div className="welcome-next-best-inner">
        <div className="welcome-next-best-copy">
          <p className="welcome-next-best-kicker">
            <Sparkles size={13} strokeWidth={2} aria-hidden />
            Suggested next step
          </p>
          <p className="welcome-next-best-domain">{item.domain}</p>
          <p className="welcome-next-best-message">
            {cleanMessage(item.message)}
          </p>
        </div>

        <button
          type="button"
          disabled={disabled}
          onClick={() => onPrompt(prompt)}
          className={[
            "welcome-next-best-action",
            isUrgent ? "welcome-next-best-action--urgent" : "",
          ].join(" ")}
        >
          Ask now
          <ArrowRight size={15} strokeWidth={2} aria-hidden />
        </button>
      </div>
    </div>
  );
}
