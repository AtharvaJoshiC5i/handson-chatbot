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
];

/** Extra structured analytics prompts (roaming, trend, spend). */
export const QUICK_QUESTIONS_ANALYTICS: QuickQuestion[] = [
  {
    label: "Roaming spend",
    message: "How much did I spend on roaming in the last 6 months?",
    icon: Globe,
  },
  {
    label: "Bill trend",
    message: "Show my bill trend over the last 6 months.",
    icon: TrendingUp,
  },
  {
    label: "Recent spend",
    message: "How much have I spent on my last 3 bills?",
    icon: ChartNoAxesColumnIncreasing,
  },
];
