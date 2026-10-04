import {
  ChartNoAxesColumnIncreasing,
  CreditCard,
  Headphones,
  ReceiptText,
  Wallet,
} from "lucide-react";

interface QuickActionRailProps {
  onAction: (prompt: string) => void;
  disabled?: boolean;
  planType?: string | null;
}

const ACTIONS = [
  {
    id: "plan",
    label: "Plan",
    icon: CreditCard,
    prompt: "Check my current plan",
  },
  {
    id: "usage",
    label: "Usage",
    icon: ChartNoAxesColumnIncreasing,
    prompt: "Review my data usage",
  },
  {
    id: "bills",
    label: "Bills",
    icon: ReceiptText,
    prompt: "Show my latest bill",
  },
  {
    id: "payments",
    label: "Payments",
    icon: Wallet,
    prompt: "Show my recent payments",
  },
  {
    id: "support",
    label: "Support",
    icon: Headphones,
    prompt: "Show my support tickets",
  },
] as const;

export function QuickActionRail({
  onAction,
  disabled = false,
  planType,
}: QuickActionRailProps) {
  return (
    <div
      className="flex gap-1 overflow-x-auto pb-1 scrollbar-none"
      aria-label="Quick actions"
    >
      {ACTIONS.map((action) => {
        const Icon = action.icon;
        let prompt: string = action.prompt;

        if (planType && action.id === "usage") {
          prompt = `Review my ${planType.toLowerCase()} data usage`;
        }

        if (planType && action.id === "bills") {
          prompt = `Show my ${planType.toLowerCase()} bill`;
        }

        return (
          <button
            key={action.id}
            type="button"
            disabled={disabled}
            onClick={() => onAction(prompt)}
            className={[
              "flex min-w-[72px] shrink-0 flex-col items-center gap-1 rounded-lg border border-[#e1e8e2]",
              "bg-white px-2 py-2 text-[9px] font-semibold text-[#41594a]",
              "transition hover:border-[#b6c9bb] hover:bg-[#fcfdfb]",
              "disabled:opacity-40",
            ].join(" ")}
          >
            <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
            {action.label}
          </button>
        );
      })}
    </div>
  );
}
