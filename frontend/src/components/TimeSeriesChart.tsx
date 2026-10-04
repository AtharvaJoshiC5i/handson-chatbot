import { useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TimeSeriesPresentation } from "../types/chat";
import { chartPresentationShell } from "../lib/presentationStyles";

interface TimeSeriesChartProps {
  presentation: TimeSeriesPresentation;
}

function formatSeriesValue(
  value: number,
  presentation: TimeSeriesPresentation,
): string {
  if (presentation.value_format === "inr") {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  }

  return `${new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(value)} ${presentation.unit}`.trim();
}

function formatAxisValue(
  value: number,
  presentation: TimeSeriesPresentation,
): string {
  const compact = new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);

  return presentation.value_format === "inr" ? `₹${compact}` : compact;
}

function computeYDomain(values: number[]): [number, number] {
  if (values.length === 0) {
    return [0, 1];
  }

  const min = Math.min(...values);
  const max = Math.max(...values);

  if (min === max) {
    const pad = Math.max(Math.abs(min) * 0.08, 1);
    return [Math.max(0, min - pad), max + pad];
  }

  const spread = max - min;
  const pad = Math.max(spread * 0.15, 1);

  return [Math.max(0, min - pad), max + pad];
}

function formatDelta(
  first: number,
  last: number,
  presentation: TimeSeriesPresentation,
): { text: string; tone: "up" | "down" | "flat" } {
  const delta = last - first;

  if (Math.abs(delta) < 0.005) {
    return { text: "No change", tone: "flat" };
  }

  const pct = first !== 0 ? (delta / first) * 100 : 0;
  const sign = delta > 0 ? "+" : "−";
  const valueText = presentation.value_format === "inr"
    ? new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }).format(Math.abs(delta))
    : `${new Intl.NumberFormat("en-IN", {
        maximumFractionDigits: 1,
      }).format(Math.abs(delta))} ${presentation.unit}`;

  const pctSign = pct >= 0 ? "+" : "−";

  return {
    text: `${sign}${valueText}${first !== 0 ? ` (${pctSign}${Math.abs(pct).toFixed(1)}%)` : ""}`,
    tone: delta > 0 ? "up" : "down",
  };
}

const DELTA_TONE_CLASS = {
  up: "bg-emerald-50/90 text-emerald-800",
  down: "bg-rose-50/90 text-rose-800",
  flat: "bg-stone-100/90 text-stone-600",
} as const;

const TOOLTIP_STYLE = {
  border: "none",
  borderRadius: 12,
  color: "#1c1917",
  fontSize: 12,
  padding: "10px 14px",
  boxShadow: "0 12px 32px rgb(23 60 50 / 0.12)",
  background: "rgba(255, 255, 255, 0.98)",
} as const;

export function TimeSeriesChart({
  presentation,
}: TimeSeriesChartProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const chartData = presentation.points;
  const values = chartData.map((point) => point.value);
  const yDomain = useMemo(() => computeYDomain(values), [values]);
  const hasDetail = chartData.some((point) => point.detail);
  const isCompactSeries = chartData.length <= 6 && !hasDetail;

  const first = values[0] ?? 0;
  const last = values[values.length - 1] ?? 0;
  const delta = formatDelta(first, last, presentation);

  const chartHeightClass =
    chartData.length <= 4 ? "h-[200px] sm:h-[220px]" : "h-[236px] sm:h-[260px]";

  return (
    <section className={chartPresentationShell}>
      <div className="px-5 pt-5 pb-1">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            {presentation.title && (
              <h3 className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted/90">
                {presentation.title}
              </h3>
            )}
            <p className="mt-1.5 text-xl font-semibold tabular-nums tracking-tight text-ink">
              {formatSeriesValue(last, presentation)}
              <span className="ml-2 text-xs font-normal text-muted">
                latest
              </span>
            </p>
          </div>
          {chartData.length > 1 && (
            <span
              className={[
                "inline-flex shrink-0 items-center rounded-full px-2.5 py-1",
                "text-[10px] font-semibold tabular-nums shadow-sm",
                DELTA_TONE_CLASS[delta.tone],
              ].join(" ")}
            >
              {delta.text}
            </span>
          )}
        </div>
      </div>

      <div
        className={[
          "w-full bg-gradient-to-b from-canvas/40 to-transparent",
          "px-2 pb-2 pt-2 sm:px-4",
          chartHeightClass,
        ].join(" ")}
        role="img"
        aria-label={`${presentation.title || "History chart"}. ${presentation.points.length} periods.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          {presentation.chart_type === "line" ? (
            <LineChart
              data={chartData}
              margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                stroke="rgba(120, 113, 108, 0.12)"
                strokeDasharray="4 6"
                vertical={false}
              />
              <XAxis
                dataKey="period"
                tick={{ fill: "#a8a29e", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                minTickGap={12}
                interval="preserveStartEnd"
              />
              <YAxis
                width={48}
                domain={yDomain}
                tick={{ fill: "#a8a29e", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) =>
                  formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) =>
                  formatSeriesValue(Number(value), presentation)}
                labelFormatter={(label) => String(label)}
                contentStyle={TOOLTIP_STYLE}
                cursor={{
                  stroke: "rgba(15, 118, 110, 0.25)",
                  strokeWidth: 1,
                  strokeDasharray: "4 4",
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                name={presentation.unit}
                stroke="#0d9488"
                strokeWidth={2.25}
                activeDot={{
                  r: 5,
                  fill: "#0f766e",
                  stroke: "#ffffff",
                  strokeWidth: 2,
                }}
                dot={{
                  r: 3.5,
                  fill: "#ffffff",
                  stroke: "#0f766e",
                  strokeWidth: 2,
                }}
              />
            </LineChart>
          ) : (
            <BarChart
              data={chartData}
              margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                stroke="rgba(120, 113, 108, 0.12)"
                strokeDasharray="4 6"
                vertical={false}
              />
              <XAxis
                dataKey="period"
                tick={{ fill: "#a8a29e", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                minTickGap={12}
              />
              <YAxis
                width={48}
                domain={yDomain}
                tick={{ fill: "#a8a29e", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) =>
                  formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) =>
                  formatSeriesValue(Number(value), presentation)}
                contentStyle={TOOLTIP_STYLE}
                cursor={{ fill: "rgba(15, 118, 110, 0.06)" }}
              />
              <Bar
                dataKey="value"
                name="Amount"
                fill="#0d9488"
                radius={[6, 6, 0, 0]}
                maxBarSize={48}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {isCompactSeries ? (
        <div
          className={[
            "grid gap-2 px-5 pb-5 pt-1",
            chartData.length <= 4
              ? "grid-cols-2 sm:grid-cols-4"
              : "grid-cols-2 sm:grid-cols-3",
          ].join(" ")}
        >
          {chartData.map((point, index) => (
            <div
              key={`${point.period}-${index}`}
              className="rounded-xl bg-canvas/60 px-2.5 py-2"
            >
              <p className="truncate text-[10px] font-medium text-muted">
                {point.period}
              </p>
              <p className="mt-0.5 text-[12px] font-semibold tabular-nums text-ink">
                {formatSeriesValue(point.value, presentation)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="mx-4 mb-4 mt-1 overflow-hidden rounded-xl bg-canvas/50">
          <button
            type="button"
            onClick={() => setShowBreakdown((open) => !open)}
            className={[
              "flex w-full items-center justify-between gap-2 px-4 py-3",
              "text-left text-[11px] font-semibold text-ink",
              "transition-colors hover:bg-canvas/80",
            ].join(" ")}
            aria-expanded={showBreakdown}
          >
            <span>
              Period breakdown
              <span className="ml-1.5 font-normal text-muted">
                ({chartData.length})
              </span>
            </span>
            <ChevronDown
              size={14}
              className={[
                "shrink-0 text-muted transition",
                showBreakdown ? "rotate-180" : "",
              ].join(" ")}
              aria-hidden="true"
            />
          </button>
          {showBreakdown && (
            <div className="divide-y divide-stone-200/50">
              {chartData.map((point, index) => (
                <div
                  key={`${point.period}-${index}`}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-2.5"
                >
                  <span className="min-w-0 truncate text-[11px] text-muted">
                    {point.period}
                  </span>
                  <div className="text-right">
                    <span className="text-[11px] font-semibold tabular-nums text-ink">
                      {formatSeriesValue(point.value, presentation)}
                    </span>
                    {point.detail && (
                      <p className="mt-0.5 text-[10px] text-muted">
                        {point.detail}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
