import type { LucideIcon } from "lucide-react";
import {
  ChartNoAxesColumnIncreasing,
  CircleHelp,
  CreditCard,
  Headphones,
  ReceiptText,
  Wifi,
} from "lucide-react";

import type { AccountSnapshot } from "../types/account";

export interface StarterPrompt {
  title: string;
  description: string;
  prompt: string;
  icon: LucideIcon;
  tone: string;
}

const BASE_PROMPTS: StarterPrompt[] = [
  {
    title: "Your plan",
    description: "See the plan and features on your account",
    prompt: "Check my current plan",
    icon: CreditCard,
    tone: "bg-[#e8f1eb] text-[#28624c]",
  },
  {
    title: "Data & usage",
    description: "Review your usage for this cycle",
    prompt: "Review my data usage",
    icon: ChartNoAxesColumnIncreasing,
    tone: "bg-[#eff1e8] text-[#586c35]",
  },
  {
    title: "Latest bill",
    description: "Find a charge or check your bill details",
    prompt: "Show my latest bill",
    icon: ReceiptText,
    tone: "bg-[#f5eee5] text-[#95652d]",
  },
  {
    title: "Payment support",
    description: "Get help with a payment or payment method",
    prompt: "Help with a payment",
    icon: CircleHelp,
    tone: "bg-[#eaf0f1] text-[#426578]",
  },
];

export function buildStarterPrompts(
  snapshot: AccountSnapshot | null,
  planTypeFilter: string | null,
): StarterPrompt[] {
  if (!snapshot) {
    return BASE_PROMPTS;
  }

  const prompts: StarterPrompt[] = [];
  const mobileSub = snapshot.active_subscriptions.find(
    (sub) => sub.plan_type === "MOBILE",
  );
  const fiberSub = snapshot.active_subscriptions.find(
    (sub) => sub.plan_type === "FIBER",
  );
  const hasMultiSub = snapshot.active_subscriptions.length > 1;

  const billStatus = snapshot.bill?.status?.toUpperCase() ?? "";
  const paymentStatus = snapshot.payment?.status?.toUpperCase() ?? "";

  if (billStatus === "UNPAID" || billStatus === "OVERDUE") {
    prompts.push({
      title: "Current bill & due date",
      description: "Amount due and when payment is expected",
      prompt: planTypeFilter
        ? `Show my ${planTypeFilter.toLowerCase()} bill`
        : "What is my current bill and due date?",
      icon: ReceiptText,
      tone: "bg-[#f5eee5] text-[#95652d]",
    });
  }

  if (paymentStatus === "FAILED") {
    prompts.push({
      title: "Why did my payment fail?",
      description: "Latest payment outcome and next steps",
      prompt: "Why did my last payment fail?",
      icon: CircleHelp,
      tone: "bg-[#fdecea] text-[#8b3a32]",
    });
  }

  if (hasMultiSub) {
    prompts.push({
      title: mobileSub ? "Mobile bill" : "Service bills",
      description: "Break down charges by service line",
      prompt: mobileSub
        ? "Show my mobile bill"
        : "List my subscriptions",
      icon: Wifi,
      tone: "bg-[#e8eef5] text-[#3d5678]",
    });

    if (fiberSub) {
      prompts.push({
        title: "Fiber usage",
        description: "Unlimited fiber usage this month",
        prompt: "Review my fiber data usage",
        icon: ChartNoAxesColumnIncreasing,
        tone: "bg-[#eff1e8] text-[#586c35]",
      });
    }
  }

  if (snapshot.attention_items.some((item) => item.domain === "Support")) {
    prompts.push({
      title: "Open support ticket",
      description: "Status and updates on your request",
      prompt: "Show my open support tickets",
      icon: Headphones,
      tone: "bg-[#eaf0f1] text-[#426578]",
    });
  }

  for (const base of BASE_PROMPTS) {
    if (prompts.length >= 6) {
      break;
    }

    if (!prompts.some((item) => item.prompt === base.prompt)) {
      prompts.push(base);
    }
  }

  return prompts.slice(0, 6);
}
