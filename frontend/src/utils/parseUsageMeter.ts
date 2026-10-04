import type { KeyValueItem } from "../types/chat";

export function parseUsageFromKeyValue(
  items: KeyValueItem[],
): { usedGb: number; limitGb: number; isUnlimited: boolean } | null {
  let usedGb: number | null = null;
  let limitGb: number | null = null;
  let isUnlimited = false;

  for (const item of items) {
    const label = item.label.toLowerCase();
    const value = item.value.toLowerCase();

    if (value.includes("unlimited")) {
      isUnlimited = true;
    }

    const gbMatch = item.value.match(/([\d.]+)\s*GB/i);

    if (!gbMatch) {
      continue;
    }

    const amount = Number.parseFloat(gbMatch[1]);

    if (!Number.isFinite(amount)) {
      continue;
    }

    if (
      label.includes("used")
      || label.includes("consumed")
      || label.includes("data used")
    ) {
      usedGb = amount;
    }

    if (
      label.includes("limit")
      || label.includes("allowance")
      || label.includes("included")
    ) {
      limitGb = amount;
    }
  }

  if (usedGb === null) {
    return null;
  }

  return {
    usedGb,
    limitGb: limitGb ?? (isUnlimited ? 0 : 1),
    isUnlimited,
  };
}
