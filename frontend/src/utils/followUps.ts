import type { ChatPresentation } from "../types/chat";

function normalize(text: string): string {
  return text.toLowerCase().replace(/\s+/g, " ").trim();
}

function isTooSimilar(suggestion: string, userMessage: string): boolean {
  const a = normalize(suggestion);
  const b = normalize(userMessage);
  if (!a || !b) {
    return false;
  }
  return a === b || a.includes(b) || b.includes(a);
}

function presentationTitle(
  presentation: ChatPresentation | null | undefined,
): string {
  if (!presentation || !("title" in presentation)) {
    return "";
  }
  const title = presentation.title;
  return typeof title === "string" ? title.toLowerCase() : "";
}

function rotatePick(
  items: string[],
  seed: string,
  count: number,
): string[] {
  const unique = [...new Set(items)];
  if (unique.length <= count) {
    return unique;
  }
  let offset = 0;
  for (let i = 0; i < seed.length; i += 1) {
    offset += seed.charCodeAt(i);
  }
  offset %= unique.length;
  const picked: string[] = [];
  for (let i = 0; i < count; i += 1) {
    picked.push(unique[(offset + i) % unique.length]);
  }
  return picked;
}

function collectFromUserMessage(userMessage: string): string[] {
  const u = normalize(userMessage);
  const out: string[] = [];

  if (
    /\b(overview|customer 360|360)\b/.test(u)
    || /\bsummary of my account\b/.test(u)
  ) {
    out.push(
      "Is anything on my account in need of attention?",
      "What is my current bill and payment status?",
      "How am I doing on my plan and data allowance?",
    );
  }

  if (
    /\battention\b/.test(u)
    || /\bneed(s)? (my )?attention\b/.test(u)
  ) {
    out.push(
      "Show my open support cases",
      "Did my last payment fail?",
      "Show my unpaid bills",
    );
  }

  if (
    /\b(bill trend|trend).{0,20}bill\b/.test(u)
    || /\bbill.{0,20}(trend|history)\b/.test(u)
    || /\blast \d+ bills\b/.test(u)
  ) {
    out.push(
      "Compare my latest bill with the previous one",
      "Break down my current bill",
      "Show my last 5 bills",
    );
  }

  if (
    /\b(break down|breakdown)\b/.test(u)
    || /\bbill charges\b/.test(u)
  ) {
    out.push(
      "Why did my bill change from last month?",
      "Reconcile my current bill and payments",
      "Compare my latest bill with the previous one",
    );
  }

  if (
    /\bcompare\b/.test(u)
    && /\bbill\b/.test(u)
  ) {
    out.push(
      "Break down my latest bill",
      "Show my last 5 bills",
      "Why did my bill change from last month?",
    );
  }

  if (
    /\b(current bill|latest bill|my bill)\b/.test(u)
    || /\bbill bill\d+\b/.test(u)
    || /\bbill0\d+\b/.test(u)
  ) {
    out.push(
      "Break down my current bill",
      "Compare my latest bill with the previous one",
      "What will my bill be this month?",
      "How much is still outstanding on my current bill?",
    );
  }

  if (
    /\b(projected|estimate).{0,12}bill\b/.test(u)
    || /\bbill be this month\b/.test(u)
  ) {
    out.push(
      "Show my latest bill",
      "Break down my current bill",
      "Show my data usage this month",
    );
  }

  if (
    /\broaming\b/.test(u)
    || /\bcharge summary\b/.test(u)
    || /\btax\b/.test(u)
    || /\bspent on my last\b/.test(u)
    || /\baverage bill\b/.test(u)
  ) {
    out.push(
      "Compare my latest bill with the previous one",
      "Show my last 5 bills",
      "Break down my current bill",
    );
  }

  if (
    /\b(payment history|recent payments|last \d+ payments)\b/.test(u)
    || /\bpayments?\b/.test(u)
  ) {
    out.push(
      "What is the status of my latest payment?",
      "Reconcile my current bill and payments",
      "Show my last 5 payments",
      "Is autopay enabled?",
    );
  }

  if (
    /\bfail(ed)?\b/.test(u)
    && /\bpayment\b/.test(u)
  ) {
    out.push(
      "Show my payment profile",
      "Do I have any account credits?",
      "Reconcile my current bill and payments",
    );
  }

  if (
    /\b(outstanding|reconcile)\b/.test(u)
  ) {
    out.push(
      "Show my last 5 payments",
      "Break down my current bill",
      "Show my unpaid bills",
    );
  }

  if (
    /\b(data usage|data used|how much data)\b/.test(u)
    || (/\bdata\b/.test(u) && /\busage\b/.test(u))
  ) {
    out.push(
      "How much data do I have remaining?",
      "What percentage of my data allowance have I used?",
      "Show my data usage history for the last 6 months",
      "Summarize my usage this month",
    );
  }

  if (
    /\b(usage trend|usage history)\b/.test(u)
    || /\btrend\b/.test(u)
    && /\busage\b/.test(u)
  ) {
    out.push(
      "Show my data usage history for the last 6 months",
      "How much data have I used this month?",
      "Summarize my usage this month",
    );
  }

  if (
    /\b(remaining|allowance|percentage)\b/.test(u)
    && /\b(data|usage)\b/.test(u)
  ) {
    out.push(
      "Summarize my usage this month",
      "Show my data usage history for the last 3 months",
      "Review my data usage",
    );
  }

  if (
    /\b(voice|minutes|sms)\b/.test(u)
  ) {
    out.push(
      "Compare my voice usage this month with last month",
      "Show my voice usage history for the last 6 months",
      "Summarize all my usage for last month",
    );
  }

  if (
    /\busage\b/.test(u)
    && !/\bbill\b/.test(u)
    && !/\bpayment\b/.test(u)
  ) {
    out.push(
      "How much data have I used this month?",
      "How much data do I have remaining?",
      "Show my data usage history for the last 6 months",
    );
  }

  if (
    /\b(support|ticket|tkt)\b/.test(u)
  ) {
    out.push(
      "Do I have any unresolved tickets?",
      "Do I have any billing-related support tickets?",
      "Summarize my support history",
    );
  }

  if (
    /\b(plan|subscription|renew)\b/.test(u)
  ) {
    out.push(
      "When does my plan renew?",
      "How much data have I used this month?",
      "Show my latest bill",
    );
  }

  if (
    /\b(account status|active|suspended)\b/.test(u)
  ) {
    out.push(
      "What plan and subscription do I have?",
      "What is my current bill and payment status?",
      "Give me an overview of my account",
    );
  }

  if (
    /\b(device|router|phone)\b/.test(u)
  ) {
    out.push(
      "How many active devices do I have?",
      "Summarize devices on my account",
      "What services are on my account?",
    );
  }

  if (
    /\b(mobile|fiber)\b/.test(u)
    && /\bbill\b/.test(u)
  ) {
    out.push(
      "Show my latest bill",
      "What services are on my account?",
      "Break down my current bill",
    );
  }

  return out;
}

function collectFromPresentation(
  presentation: ChatPresentation | null | undefined,
): string[] {
  if (!presentation) {
    return [];
  }

  const out: string[] = [];
  const title = presentationTitle(presentation);

  if (
    presentation.type === "key_value"
    && presentation.items.some((item) =>
      item.label.toLowerCase().includes("bill id"),
    )
  ) {
    out.push(
      "Break down this bill",
      "Compare this bill to last month",
    );
  }

  if (title.includes("payment history")) {
    out.push(
      "Reconcile my current bill and payments",
      "What is the status of my latest payment?",
    );
  }

  if (
    presentation.type === "time_series"
    && (title.includes("usage") || title.includes("data") || title.includes("voice"))
  ) {
    out.push(
      "How much data do I have remaining?",
      "Summarize my usage this month",
    );
  }

  if (
    presentation.type === "time_series"
    && title.includes("bill")
  ) {
    out.push(
      "Compare my latest bill with the previous one",
      "Break down my current bill",
    );
  }

  if (presentation.type === "comparison") {
    out.push(
      "Why did my bill change from last month?",
      "Show my last 5 bills",
    );
  }

  return out;
}

export function suggestedFollowUps(
  presentation: ChatPresentation | null | undefined,
  userMessage: string,
): string[] {
  const user = userMessage.trim();
  if (!user) {
    return [];
  }

  const pooled = [
    ...collectFromUserMessage(user),
    ...collectFromPresentation(presentation),
  ];

  const filtered = pooled.filter(
    (suggestion) => !isTooSimilar(suggestion, user),
  );

  if (filtered.length === 0) {
    return [];
  }

  return rotatePick(filtered, user, 3);
}
