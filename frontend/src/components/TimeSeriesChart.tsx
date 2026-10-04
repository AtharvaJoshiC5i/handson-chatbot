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
import { presentationShell } from "../lib/presentationStyles";

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

export function TimeSeriesChart({
  presentation,
}: TimeSeriesChartProps) {
  const chartData = presentation.points;

  return (
    <section className={presentationShell}>
      {presentation.title && (
        <h3 className="border-b border-line px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted">
          {presentation.title}
        </h3>
      )}
      <div
        className="h-[236px] w-full px-2 pb-2 pt-4 sm:h-[270px] sm:px-4"
        role="img"
        aria-label={`${presentation.title || "History chart"}. ${presentation.points.length} periods.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          {presentation.chart_type === "line" ? (
            <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid stroke="#e7e5e4" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="period"
                tick={{ fill: "#78716c", fontSize: 10 }}
                axisLine={{ stroke: "#e7e5e4" }}
                tickLine={false}
                minTickGap={16}
              />
              <YAxis
                width={56}
                tick={{ fill: "#78716c", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) => formatSeriesValue(Number(value), presentation)}
                contentStyle={{
                  border: "1px solid #e7e5e4",
                  borderRadius: 8,
                  color: "#1c1917",
                  fontSize: 12,
                  boxShadow: "0 4px 14px rgb(28 25 23 / 0.08)",
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                name={presentation.unit}
                stroke="#0f766e"
                strokeWidth={2.5}
                activeDot={{ r: 5, fill: "#d97706", stroke: "#ffffff", strokeWidth: 2 }}
                dot={{ r: 3, fill: "#0f766e", stroke: "#ffffff", strokeWidth: 1.5 }}
              />
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid stroke="#e7e5e4" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="period"
                tick={{ fill: "#78716c", fontSize: 10 }}
                axisLine={{ stroke: "#e7e5e4" }}
                tickLine={false}
                minTickGap={16}
              />
              <YAxis
                width={56}
                tick={{ fill: "#78716c", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) => formatSeriesValue(Number(value), presentation)}
                contentStyle={{
                  border: "1px solid #e7e5e4",
                  borderRadius: 8,
                  color: "#1c1917",
                  fontSize: 12,
                  boxShadow: "0 4px 14px rgb(28 25 23 / 0.08)",
                }}
              />
              <Bar
                dataKey="value"
                name="Bill amount"
                fill="#0f766e"
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <div className="border-t border-line">
        {presentation.points.map((point, index) => (
          <div
            key={`${point.period}-${index}`}
            className="grid grid-cols-[minmax(0,1fr)_minmax(0,auto)_minmax(0,auto)] items-center gap-3 border-b border-line px-4 py-2.5 last:border-b-0"
          >
            <span className="min-w-0 truncate text-[11px] text-muted">{point.period}</span>
            <span className="text-right text-[11px] font-semibold tabular-nums text-ink">
              {formatSeriesValue(point.value, presentation)}
            </span>
            {point.detail && (
              <span className="text-right text-[10px] text-muted">{point.detail}</span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
