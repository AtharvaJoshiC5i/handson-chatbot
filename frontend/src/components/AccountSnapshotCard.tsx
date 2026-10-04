import type { AccountSnapshot } from "../types/account";

import { SnapshotSkeleton } from "./SnapshotSkeleton";
import { StatusChip } from "./StatusChip";
import { UsageMeter } from "./UsageMeter";
import { formatInr, formatVerifiedAt } from "../utils/accountFormat";
import { parseUsageHeadline } from "../utils/welcomePersonalization";
import { statusVariantForValue } from "../utils/statusChip";

interface AccountSnapshotCardProps {
  snapshot: AccountSnapshot | null;
  loading?: boolean;
  planTypeFilter?: string | null;
  showDataTimestamp?: boolean;
}

export function AccountSnapshotCard({
  snapshot,
  loading = false,
  planTypeFilter,
  showDataTimestamp = true,
}: AccountSnapshotCardProps) {
  if (loading) {
    return <SnapshotSkeleton />;
  }

  if (!snapshot) {
    return null;
  }

  const filteredSub = planTypeFilter
    ? snapshot.active_subscriptions.find(
        (sub) => sub.plan_type === planTypeFilter,
      )
    : null;

  const plan = filteredSub
    ? {
        plan_name: filteredSub.plan_name,
        plan_type: filteredSub.plan_type,
        renewal_date: filteredSub.renewal_date,
        data_limit_gb: snapshot.plan?.data_limit_gb ?? 0,
        is_data_unlimited:
          filteredSub.plan_type === "FIBER"
          || (snapshot.plan?.is_data_unlimited ?? false),
      }
    : snapshot.plan;

  const bill = snapshot.bill;
  const billVariant = bill
    ? statusVariantForValue(bill.status)
    : null;

  const parsedUsage = parseUsageHeadline(
    snapshot.usage_headline,
    plan,
  );

  const usedGb = parsedUsage?.usedGb ?? null;
  const limitGb =
    parsedUsage?.limitGb ?? plan?.data_limit_gb ?? null;
  const isUnlimited =
    parsedUsage?.isUnlimited ?? plan?.is_data_unlimited ?? false;

  return (
    <div className="structured-export overflow-hidden rounded-xl border border-[#dfe7e0] bg-white shadow-[0_8px_24px_rgba(23,60,50,0.05)]">
      <div className="border-b border-[#edf1ed] px-4 py-3">
        <p className="text-[11px] font-semibold text-[#526f5c]">
          Account snapshot
        </p>
        {plan && (
          <p className="mt-1 text-[13px] font-semibold text-[#1c342b]">
            {plan.plan_name}
            <span className="ml-2 text-[11px] font-medium text-[#7d8b81]">
              Renews {plan.renewal_date}
            </span>
          </p>
        )}
      </div>

      <div className="grid gap-0 divide-y divide-[#edf1ed] sm:grid-cols-2 sm:divide-x sm:divide-y-0">
        <div className="space-y-3 p-4">
          {usedGb !== null && (limitGb !== null || isUnlimited) && (
            <UsageMeter
              usedGb={usedGb}
              limitGb={limitGb ?? 0}
              isUnlimited={isUnlimited}
            />
          )}

          {snapshot.usage_headline && usedGb === null && (
            <p className="text-[12px] text-[#52665a]">
              {snapshot.usage_headline}
            </p>
          )}

          {!snapshot.has_payment_profile && (
            <p className="text-[11px] text-[#8a968d]">
              No saved payment method on file.
            </p>
          )}

          {snapshot.payment_profile && (
            <dl className="space-y-2 text-[11px]">
              <div className="flex justify-between gap-3">
                <dt className="text-[#7d8b81]">Autopay</dt>
                <dd className="font-medium text-[#2c4135]">
                  {snapshot.payment_profile.autopay_enabled
                    ? "On"
                    : "Off"}
                </dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-[#7d8b81]">Payment method</dt>
                <dd className="font-medium text-[#2c4135]">
                  {snapshot.payment_profile.payment_method_label}
                </dd>
              </div>
            </dl>
          )}
        </div>

        <div className="space-y-3 p-4">
          {bill && (
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
                Current bill
              </p>
              <p className="mt-1 text-[22px] font-semibold tabular-nums text-[#1c342b]">
                {formatInr(bill.amount)}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {billVariant && (
                  <StatusChip
                    label={bill.status}
                    variant={billVariant}
                  />
                )}
                <span className="text-[11px] text-[#7d8b81]">
                  Due {bill.due_date}
                </span>
              </div>
            </div>
          )}

          {snapshot.projected_bill && (
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wide text-[#86938b]">
                Projected bill
              </p>
              <p className="mt-1 text-[18px] font-semibold tabular-nums text-[#1c342b]">
                {formatInr(snapshot.projected_bill.estimated_amount)}
              </p>
              <p className="text-[10px] text-[#7d8b81]">
                {snapshot.projected_bill.plan_name} · as of{" "}
                {snapshot.projected_bill.as_of_date}
              </p>
            </div>
          )}

          {snapshot.available_credits > 0 && (
            <p className="text-[11px] text-[#52665a]">
              Available credits:{" "}
              <span className="font-semibold tabular-nums">
                {formatInr(snapshot.available_credits)}
              </span>
            </p>
          )}
        </div>
      </div>

      {showDataTimestamp && (
        <p className="border-t border-[#edf1ed] px-4 py-2 text-[9px] text-[#96a198]">
          Account data as of {formatVerifiedAt(snapshot.generated_at)}
        </p>
      )}
    </div>
  );
}
