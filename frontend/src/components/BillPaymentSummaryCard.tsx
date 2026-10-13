import type { SummaryPresentation } from "../types/chat";

interface BillPaymentSummaryCardProps {
  presentation: SummaryPresentation;
}

export function isBillPaymentSummaryPresentation(
  presentation: SummaryPresentation,
): boolean {
  const title = presentation.title?.toLowerCase() ?? "";

  return title.includes("bill") && title.includes("payment");
}

export function BillPaymentSummaryCard({
  presentation,
}: BillPaymentSummaryCardProps) {
  const outstanding = presentation.sections.find(
    (section) => section.label === "Outstanding",
  );
  const bill = presentation.sections.find(
    (section) => section.label === "Bill",
  );

  return (
    <div className="overflow-hidden rounded-xl border border-[#dce6de] bg-white shadow-[0_2px_12px_rgba(23,60,50,0.05)]">
      <div className="border-b border-[#e8ede9] bg-gradient-to-r from-[#f4faf5] to-white px-4 py-3">
        <p className="text-[12px] font-semibold text-[#30493b]">
          {presentation.title ?? "Bill & payment"}
        </p>
        {bill?.secondary && (
          <p className="mt-0.5 text-[11px] text-[#7d8b81]">
            {bill.secondary}
          </p>
        )}
      </div>

      <div className="grid gap-0 divide-y divide-[#edf1ed] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        {presentation.sections.map((section) => (
          <div
            key={section.label}
            className="px-4 py-3.5"
          >
            <p className="text-[10px] font-medium uppercase tracking-wide text-[#96a198]">
              {section.label}
            </p>
            <p
              className={[
                "mt-1 text-[15px] font-semibold tabular-nums text-[#20392d]",
                section.label === "Outstanding"
                  && outstanding?.primary !== "₹0"
                  && outstanding?.primary !== "₹0.00"
                  ? "text-[#9a4a3a]"
                  : "",
              ].join(" ")}
            >
              {section.primary}
            </p>
            {section.secondary && (
              <p className="mt-1 text-[11px] leading-snug text-[#7d8b81]">
                {section.secondary}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
