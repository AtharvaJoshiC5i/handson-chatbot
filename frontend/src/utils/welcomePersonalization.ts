import type { AccountSnapshot } from "../types/account";
import type { QuickQuestion } from "./quickQuestions";

export interface ParsedUsage {
  usedGb: number;
  limitGb: number;
  isUnlimited: boolean;
  percent?: number;
}

export function greetingForLocalHour(
  date = new Date(),
): string {
  const hour = date.getHours();

  if (hour < 12) {
    return "Good morning";
  }

  if (hour < 17) {
    return "Good afternoon";
  }

  return "Good evening";
}

export function formatDisplayDate(
  value: string | null | undefined,
): string | null {
  if (!value?.trim()) {
    return null;
  }

  const raw = value.trim();
  const normalized = raw.includes("T")
    ? raw
    : `${raw}T12:00:00`;

  const parsed = new Date(normalized);

  if (Number.isNaN(parsed.getTime())) {
    return raw.split("T")[0] ?? raw;
  }

  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function parseUsageHeadline(
  headline: string | null | undefined,
  plan: AccountSnapshot["plan"],
): ParsedUsage | null {
  if (!headline?.trim()) {
    return null;
  }

  const capped = headline.trim();
  const ratio = capped.match(
    /([\d.]+)\s*\/\s*([\d.]+)\s*GB/i,
  );

  if (ratio) {
    const usedGb = Number.parseFloat(ratio[1]);
    const limitGb = Number.parseFloat(ratio[2]);
    const percentMatch = capped.match(/\(([\d.]+)%\)/);

    return {
      usedGb,
      limitGb,
      isUnlimited: false,
      percent: percentMatch
        ? Number.parseFloat(percentMatch[1])
        : undefined,
    };
  }

  const unlimited = capped.match(
    /([\d.]+)\s*GB used/i,
  );

  if (unlimited || plan?.is_data_unlimited) {
    const usedGb = unlimited
      ? Number.parseFloat(unlimited[1])
      : 0;

    return {
      usedGb,
      limitGb: plan?.data_limit_gb ?? 0,
      isUnlimited: true,
    };
  }

  return null;
}

function primarySubscription(
  snapshot: AccountSnapshot,
) {
  if (snapshot.plan) {
    const match = snapshot.active_subscriptions.find(
      (sub) => sub.plan_name === snapshot.plan?.plan_name,
    );
    return match ?? snapshot.active_subscriptions[0] ?? null;
  }

  return snapshot.active_subscriptions[0] ?? null;
}

export function buildWelcomeLead(
  snapshot: AccountSnapshot,
): string {
  const planName = snapshot.plan?.plan_name;
  const renewal = formatDisplayDate(
    snapshot.plan?.renewal_date,
  );
  const bill = snapshot.bill;

  if (bill?.status === "UNPAID" || bill?.status === "OVERDUE") {
    const due = formatDisplayDate(bill.due_date);
    return `Your latest bill of ₹${Math.round(bill.amount).toLocaleString("en-IN")}${due ? ` is due ${due}` : " needs attention"}.`;
  }

  if (snapshot.payment?.status === "FAILED") {
    return "Your most recent payment did not go through — review payment status when you're ready.";
  }

  if (planName && renewal) {
    return `${planName} is active on your account. Renewal is scheduled for ${renewal}.`;
  }

  if (planName) {
    return `${planName} is the plan currently linked to your usage and billing.`;
  }

  return "Ask anything about your plan, usage, bills, payments, and support history.";
}

export function accountStatusLabel(
  status: string,
): string {
  return status
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/^\w/, (c) => c.toUpperCase());
}

export function accountStatusTone(
  accountStatus: string,
): "active" | "suspended" | "neutral" {
  const normalized = accountStatus.toUpperCase();

  if (normalized === "ACTIVE") {
    return "active";
  }

  if (normalized === "SUSPENDED" || normalized === "CANCELLED") {
    return "suspended";
  }

  return "neutral";
}

export function billStatusTone(
  status: string,
): "paid" | "due" | "neutral" {
  const normalized = status.toUpperCase();

  if (normalized === "PAID") {
    return "paid";
  }

  if (
    normalized === "UNPAID"
    || normalized === "OVERDUE"
    || normalized === "PARTIAL"
  ) {
    return "due";
  }

  return "neutral";
}

export function prioritizeQuickQuestions(
  items: QuickQuestion[],
  snapshot: AccountSnapshot,
): QuickQuestion[] {
  const domains = new Set(
    snapshot.attention_items.map((item) =>
      item.domain.toLowerCase(),
    ),
  );

  const score = (item: QuickQuestion): number => {
    const message = item.message.toLowerCase();
    let value = 0;

    if (domains.has("billing") && message.includes("bill")) {
      value += 3;
    }

    if (domains.has("payments") && message.includes("payment")) {
      value += 3;
    }

    if (domains.has("usage") && message.includes("usage")) {
      value += 2;
    }

    if (domains.has("support") && message.includes("support")) {
      value += 2;
    }

    if (snapshot.bill?.status === "UNPAID" && message.includes("bill")) {
      value += 2;
    }

    return value;
  };

  return [...items].sort(
    (left, right) => score(right) - score(left),
  );
}

export function welcomeQuickSectionTitle(
  snapshot: AccountSnapshot,
  firstName: string,
): string {
  const plan = snapshot.plan?.plan_name;

  if (plan) {
    return `Ask about ${plan}`;
  }

  return `Suggested for ${firstName}`;
}

export function personalAssistantTagline(
  firstName: string,
): string {
  return `Your assistant for ${firstName} — only this account’s records.`;
}

export function personalQuickPromptTitle(
  firstName: string,
  snapshot: AccountSnapshot | null,
): string {
  const plan = snapshot?.plan?.plan_name;

  if (plan) {
    return `${firstName}, ask about ${plan}`;
  }

  return `${firstName}, what can I help with?`;
}

export function subscriptionMonthlyPrice(
  snapshot: AccountSnapshot,
): number | null {
  const sub = primarySubscription(snapshot);
  return sub?.monthly_price ?? null;
}

export function serviceLocationLine(
  snapshot: AccountSnapshot,
): string | null {
  const address = snapshot.service_address_line?.trim();
  const city = snapshot.city?.trim();

  if (address && city) {
    return `${address}, ${city}`;
  }

  if (address) {
    return address;
  }

  if (city) {
    return city;
  }

  return null;
}
