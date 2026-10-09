import type { LucideIcon } from "lucide-react";
import {
  ChartNoAxesColumnIncreasing,
  CreditCard,
  Globe,
  Headphones,
  ReceiptText,
  TrendingUp,
  Wallet,
} from "lucide-react";

export interface QuickQuestion {
  label: string;
  message: string;
  icon: LucideIcon;
}

/** Deduplicated starter prompts for the empty chat state. */
export const QUICK_QUESTIONS_TO_GET_STARTED: QuickQuestion[] = [
  {
    label: "Current plan",
    message: "Check my current plan",
    icon: CreditCard,
  },
  {
    label: "Data usage",
    message: "Review my data usage",
    icon: ChartNoAxesColumnIncreasing,
  },
  {
    label: "Latest bill",
    message: "Show my latest bill",
    icon: ReceiptText,
  },
  {
    label: "Payments",
    message: "Show my recent payments",
    icon: Wallet,
  },
  {
    label: "Support",
    message: "Show my support tickets",
    icon: Headphones,
  },
  {
    label: "Bill spike",
    message: "Why is my bill higher this month?",
    icon: TrendingUp,
  },
  {
    label: "Right plan?",
    message: "Am I on the right plan?",
    icon: CreditCard,
  },
];

/** Extra structured prompts (history and compare). */
export const QUICK_QUESTIONS_ANALYTICS: QuickQuestion[] = [
  {
    label: "Compare bills",
    message: "Compare my latest bill with the previous one",
    icon: TrendingUp,
  },
  {
    label: "Bill history",
    message: "Show my last 5 bills",
    icon: ChartNoAxesColumnIncreasing,
  },
  {
    label: "Usage history",
    message: "Show my data usage history for the last 6 months",
    icon: Globe,
  },
];
