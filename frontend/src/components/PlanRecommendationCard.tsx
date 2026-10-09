import { ArrowRight, Sparkles } from "lucide-react";

import type { PlanRecommendationPresentation } from "../types/chat";
import { UsageMeter } from "./UsageMeter";

function formatInr(value: number | null | undefined): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  const rounded = Math.round(value);
  if (Math.abs(value - rounded) < 0.01) {
    return `₹${rounded.toLocaleString("en-IN")}`;
  }

  return `₹${value.toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

interface PlanTileProps {
  eyebrow: string;
  planName: string;
  dataGb: number | null | undefined;
  price: number | null | undefined;
  variant: "current" | "suggested" | "solo";
}

function PlanTile({
  eyebrow,
  planName,
  dataGb,
  price,
  variant,
}: PlanTileProps) {
  const isSuggested = variant === "suggested";

  return (
    <div
      className={[
        "plan-rec-tile",
        isSuggested ? "plan-rec-tile--suggested" : "",
        variant === "solo" ? "plan-rec-tile--solo" : "",
      ].join(" ")}
    >
      <p className="plan-rec-tile-eyebrow">{eyebrow}</p>
      <p className="plan-rec-tile-name">{planName}</p>
      <div className="plan-rec-tile-meta">
        {dataGb !== null && dataGb !== undefined && (
          <span>{dataGb.toLocaleString("en-IN")} GB</span>
        )}
        {price !== null && price !== undefined && (
          <span>{formatInr(price)}/mo</span>
        )}
      </div>
    </div>
  );
}

interface PlanRecommendationCardProps {
  presentation: PlanRecommendationPresentation;
}

export function PlanRecommendationCard({
  presentation,
}: PlanRecommendationCardProps) {
  const {
    title,
    current,
    recommended,
    average_monthly_data_gb: avgGb,
    months_sampled: monthsSampled,
    utilization_percent: utilization,
    estimated_monthly_savings: savings,
    reasons,
    recommendation_status: status,
  } = presentation;

  const showSwitch = Boolean(
    recommended?.plan_name && status !== "KEEP_CURRENT",
  );
  const usageLabel =
    monthsSampled && monthsSampled > 0
      ? `Typical usage (last ${monthsSampled} mo.)`
      : "Typical usage";

  return (
    <div className="structured-export plan-rec-card">
      <div className="plan-rec-header">
        <div className="plan-rec-header-text">
          <p className="plan-rec-title">{title ?? "Plan recommendation"}</p>
          <p className="plan-rec-subtitle">
            {showSwitch
              ? "Based on how you use data on this line"
              : "Your recent usage compared to your allowance"}
          </p>
        </div>
        {savings !== null && savings !== undefined && savings > 0 && (
          <div className="plan-rec-savings-badge">
            <Sparkles className="plan-rec-savings-icon" aria-hidden />
            Save {formatInr(savings)}/mo
          </div>
        )}
      </div>

      <div
        className={[
          "plan-rec-plans",
          showSwitch ? "plan-rec-plans--switch" : "plan-rec-plans--solo",
        ].join(" ")}
      >
        <PlanTile
          eyebrow="Current plan"
          planName={current.plan_name}
          dataGb={current.data_limit_gb}
          price={current.monthly_price}
          variant={showSwitch ? "current" : "solo"}
        />
        {showSwitch && recommended && (
          <>
            <div className="plan-rec-arrow" aria-hidden>
              <ArrowRight className="h-4 w-4" strokeWidth={2} />
            </div>
            <PlanTile
              eyebrow="Suggested plan"
              planName={recommended.plan_name}
              dataGb={recommended.data_limit_gb}
              price={recommended.monthly_price}
              variant="suggested"
            />
          </>
        )}
      </div>

      {avgGb !== null
        && avgGb !== undefined
        && current.data_limit_gb !== null
        && current.data_limit_gb !== undefined
        && current.data_limit_gb > 0 && (
        <div className="plan-rec-usage">
          <UsageMeter
            compact
            usedGb={avgGb}
            limitGb={current.data_limit_gb}
            label={usageLabel}
            className="plan-rec-usage-meter"
          />
          {utilization !== null && utilization !== undefined && (
            <p className="plan-rec-utilization">
              You typically use{" "}
              <strong>{utilization.toLocaleString("en-IN")}%</strong> of your
              monthly allowance.
            </p>
          )}
        </div>
      )}

      {reasons.length > 0 && (
        <div className="plan-rec-insights">
          <p className="plan-rec-insights-label">Why we recommend this</p>
          <ul className="plan-rec-insights-list">
            {reasons.map((reason, index) => (
              <li key={`${index}-${reason.slice(0, 24)}`}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
