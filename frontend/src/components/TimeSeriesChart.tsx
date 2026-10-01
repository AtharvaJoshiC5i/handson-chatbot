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
    <section className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      {presentation.title && (
        <h3 className="border-b border-[#e8ede9] px-4 py-3 text-[12px] font-semibold text-[#30493b]">
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
              <CartesianGrid stroke="#e8eee9" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="period"
                tick={{ fill: "#728177", fontSize: 10 }}
                axisLine={{ stroke: "#dfe7e0" }}
                tickLine={false}
                minTickGap={16}
              />
              <YAxis
                width={56}
                tick={{ fill: "#829087", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) => formatSeriesValue(Number(value), presentation)}
                contentStyle={{
                  border: "1px solid #dfe7e0",
                  borderRadius: 8,
                  color: "#2c4135",
                  fontSize: 12,
                  boxShadow: "0 4px 14px rgba(23,60,50,0.08)",
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                name={presentation.unit}
                stroke="#347052"
                strokeWidth={2.5}
                activeDot={{ r: 5, fill: "#d3a451", stroke: "#ffffff", strokeWidth: 2 }}
                dot={{ r: 3, fill: "#347052", stroke: "#ffffff", strokeWidth: 1.5 }}
              />
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
              <CartesianGrid stroke="#e8eee9" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="period"
                tick={{ fill: "#728177", fontSize: 10 }}
                axisLine={{ stroke: "#dfe7e0" }}
                tickLine={false}
                minTickGap={16}
              />
              <YAxis
                width={56}
                tick={{ fill: "#829087", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => formatAxisValue(value, presentation)}
              />
              <Tooltip
                formatter={(value) => formatSeriesValue(Number(value), presentation)}
                contentStyle={{
                  border: "1px solid #dfe7e0",
                  borderRadius: 8,
                  color: "#2c4135",
                  fontSize: 12,
                  boxShadow: "0 4px 14px rgba(23,60,50,0.08)",
                }}
              />
              <Bar
                dataKey="value"
                name="Bill amount"
                fill="#347052"
                radius={[4, 4, 0, 0]}
                maxBarSize={40}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      <div className="border-t border-[#e8ede9]">
        {presentation.points.map((point, index) => (
          <div
            key={`${point.period}-${index}`}
            className="grid grid-cols-[minmax(0,1fr)_minmax(0,auto)_minmax(0,auto)] items-center gap-3 border-b border-[#edf1ed] px-4 py-2.5 last:border-b-0"
          >
            <span className="min-w-0 truncate text-[11px] text-[#728177]">{point.period}</span>
            <span className="text-right text-[11px] font-semibold tabular-nums text-[#2c4135]">
              {formatSeriesValue(point.value, presentation)}
            </span>
            {point.detail && (
              <span className="text-right text-[10px] text-[#7d8b81]">{point.detail}</span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
