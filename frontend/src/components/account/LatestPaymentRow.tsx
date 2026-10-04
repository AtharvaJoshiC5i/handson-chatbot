import type { AccountSnapshot } from "../../types/account";
import { StatusChip } from "../StatusChip";
import { statusVariantForValue } from "../../utils/statusChip";

interface LatestPaymentRowProps {
  snapshot: AccountSnapshot;
}

export function LatestPaymentRow({ snapshot }: LatestPaymentRowProps) {
  const payment = snapshot.payment;

  if (!payment) {
    return null;
  }

  const variant = statusVariantForValue(payment.status);

  return (
    <section
      className="account-overview-section"
      aria-label="Latest payment"
    >
      <h2 className="account-overview-section-title">Latest payment</h2>
      <div className="account-overview-list-item !rounded-xl">
        <div>
          <p className="text-[12px] font-medium text-[var(--color-ink)]">
            Most recent transaction
          </p>
          {payment.failure_reason && (
            <p className="mt-1 text-[11px] leading-snug text-[#9a4038]">
              {payment.failure_reason}
            </p>
          )}
        </div>
        {variant && (
          <StatusChip label={payment.status} variant={variant} />
        )}
      </div>
    </section>
  );
}
