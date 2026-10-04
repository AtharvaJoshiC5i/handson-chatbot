import type { AccountSnapshot } from "../../types/account";
import { formatDisplayDate } from "../../utils/welcomePersonalization";
import { formatInr, lineLabel } from "../../utils/accountFormat";

interface BillsByLineTilesProps {
  snapshot: AccountSnapshot;
  variant?: "section" | "embedded";
}

export function BillsByLineTiles({
  snapshot,
  variant = "section",
}: BillsByLineTilesProps) {
  if (snapshot.bills_by_line.length <= 1) {
    return null;
  }

  const grid = (
    <div className="welcome-line-grid !mt-0 !px-0 !pt-0">
        {snapshot.bills_by_line.map((line) => (
          <div key={line.plan_type} className="welcome-line-tile">
            <p className="welcome-section-kicker">
              {lineLabel(line.plan_type)} · {line.plan_name}
            </p>
            <p className="mt-1 text-[14px] font-semibold tabular-nums">
              {formatInr(line.amount)}
            </p>
            <p className="mt-0.5 text-[10px] text-[#6d7f73]">
              {line.bill_id} · Due {formatDisplayDate(line.due_date) ?? "—"}
            </p>
          </div>
        ))}
      </div>
  );

  if (variant === "embedded") {
    return grid;
  }

  return (
    <section
      className="account-overview-section"
      aria-label="Latest bill by connection"
    >
      <h2 className="account-overview-section-title">Bills by line</h2>
      {grid}
    </section>
  );
}
