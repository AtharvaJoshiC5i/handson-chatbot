import type { ReactNode } from "react";

import { StatusChip } from "./StatusChip";
import {
  isStatusLabel,
  statusVariantForValue,
} from "../utils/statusChip";

const ENTITY_PATTERN =
  /\b(BILL\d+|TKT\d+|PAY\d+|TXN-[A-Z0-9-]+)\b/gi;

interface StructuredValueProps {
  label: string;
  value: string;
  onEntitySelect?: (message: string) => void;
}

export function StructuredValue({
  label,
  value,
  onEntitySelect,
}: StructuredValueProps) {
  const variant =
    isStatusLabel(label)
      ? statusVariantForValue(value)
      : statusVariantForValue(value);

  if (variant && (isStatusLabel(label) || value.length < 24)) {
    return (
      <StatusChip label={value} variant={variant} />
    );
  }

  const entities = [...value.matchAll(ENTITY_PATTERN)];

  if (entities.length === 0 || !onEntitySelect) {
    return <span>{value}</span>;
  }

  const parts: ReactNode[] = [];
  let lastIndex = 0;

  for (const match of entities) {
    const entity = match[0];
    const index = match.index ?? 0;

    if (index > lastIndex) {
      parts.push(value.slice(lastIndex, index));
    }

    parts.push(
      <button
        key={`${entity}-${index}`}
        type="button"
        onClick={() => onEntitySelect(`Tell me about ${entity}`)}
        className="mx-0.5 inline rounded bg-[#edf3ef] px-1.5 py-0.5 text-[11px] font-semibold text-[#28624c] hover:bg-[#dfece4]"
      >
        {entity}
      </button>,
    );

    lastIndex = index + entity.length;
  }

  if (lastIndex < value.length) {
    parts.push(value.slice(lastIndex));
  }

  return <span>{parts}</span>;
}
