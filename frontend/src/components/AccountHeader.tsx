import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface AccountHeaderProps {
  name: string;
  phoneMasked: string;
  accountStatus: string;
  city?: string;
  planName?: string | null;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function AccountHeader({
  name,
  phoneMasked,
  accountStatus,
  city,
  planName,
}: AccountHeaderProps) {
  const statusVariant =
    statusVariantForValue(accountStatus) ?? "neutral";

  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="grid size-10 shrink-0 place-items-center rounded-full bg-[#173c32] text-[12px] font-semibold text-[#f0d69a]">
        {initials(name)}
      </span>

      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-[13px] font-semibold text-[#23352e]">
            {name}
          </span>
          <StatusChip
            label={accountStatus}
            variant={statusVariant}
          />
        </div>
        <p className="mt-0.5 truncate text-[10px] text-[#839087]">
          {phoneMasked}
          {city ? ` · ${city}` : ""}
          {planName ? ` · ${planName}` : ""}
        </p>
      </div>
    </div>
  );
}
