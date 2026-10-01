import { lazy, Suspense } from "react";

import type {
  ChatPresentation,
  ComparisonPresentation,
  Customer360Presentation,
  KeyValuePresentation,
  ListPresentation,
  SummaryPresentation,
  TablePresentation,
} from "../types/chat";

const TimeSeriesChart = lazy(() =>
  import("./TimeSeriesChart").then((module) => ({
    default: module.TimeSeriesChart,
  })),
);

interface StructuredPresentationProps {
  presentation: ChatPresentation;
}

interface PresentationTitleProps {
  title?: string | null;
}

function PresentationTitle({
  title,
}: PresentationTitleProps) {
  if (!title) {
    return null;
  }

  return (
    <div className="border-b border-[#e8ede9] px-4 py-3">
      <p className="text-[12px] font-semibold text-[#30493b]">
        {title}
      </p>
    </div>
  );
}

function KeyValueResult({
  presentation,
}: {
  presentation: KeyValuePresentation;
}) {
  if (presentation.items.length === 0) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />

      <dl className="divide-y divide-[#edf1ed]">
        {presentation.items.map((item, index) => (
          <div
            key={`${item.label}-${index}`}
            className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)] gap-4 px-4 py-3"
          >
            <dt className="min-w-0 text-[11px] leading-5 text-[#7d8b81]">
              {item.label}
            </dt>

            <dd className="min-w-0 break-words text-right text-[12px] font-medium leading-5 text-[#2c4135]">
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ComparisonResult({
  presentation,
}: {
  presentation: ComparisonPresentation;
}) {
  if (
    presentation.columns.length === 0 ||
    presentation.rows.length === 0
  ) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />

      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] border-collapse text-left">
          <thead>
            <tr className="border-b border-[#e5ebe6] bg-[#f6f8f6]">
              <th className="px-4 py-3 text-[10px] font-semibold text-[#748278]">
                Detail
              </th>

              {presentation.columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-right text-[10px] font-semibold text-[#52665a]"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-[#edf1ed]">
            {presentation.rows.map((row, rowIndex) => (
              <tr key={`${row.label}-${rowIndex}`}>
                <td className="px-4 py-3 text-[11px] leading-5 text-[#718076]">
                  {row.label}
                </td>

                {presentation.columns.map((column) => (
                  <td
                    key={column.key}
                    className="px-4 py-3 text-right text-[11px] font-medium leading-5 text-[#2c4135]"
                  >
                    {row.values[column.key] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ListResult({
  presentation,
}: {
  presentation: ListPresentation;
}) {
  if (presentation.items.length === 0) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />

      <div className="divide-y divide-[#edf1ed]">
        {presentation.items.map((item, index) => (
          <div
            key={`${item.label}-${index}`}
            className="flex min-w-0 items-start justify-between gap-5 px-4 py-3"
          >
            <div className="min-w-0 flex-1">
              <p className="break-words text-[12px] font-medium leading-5 text-[#2c4135]">
                {item.label}
              </p>

              {item.detail && (
                <p className="mt-1 break-words text-[11px] leading-5 text-[#7d8b81]">
                  {item.detail}
                </p>
              )}
            </div>

            <p className="shrink-0 text-right text-[11px] font-semibold leading-5 text-[#52665a]">
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TableResult({
  presentation,
}: {
  presentation: TablePresentation;
}) {
  if (
    presentation.columns.length === 0 ||
    presentation.rows.length === 0
  ) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />

      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] border-collapse text-left">
          <thead>
            <tr className="border-b border-[#e5ebe6] bg-[#f6f8f6]">
              {presentation.columns.map((column) => (
                <th
                  key={column.key}
                  className={[
                    "whitespace-nowrap px-4 py-3",
                    "text-[10px] font-semibold text-[#65766a]",
                    column.align === "right"
                      ? "text-right"
                      : "text-left",
                  ].join(" ")}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-[#edf1ed]">
            {presentation.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {presentation.columns.map((column) => (
                  <td
                    key={column.key}
                    className={[
                      "px-4 py-3",
                      "text-[11px] leading-5 text-[#34483b]",
                      column.align === "right"
                        ? "whitespace-nowrap text-right font-medium tabular-nums"
                        : "min-w-[120px] whitespace-normal break-words text-left",
                    ].join(" ")}
                  >
                    {row[column.key] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryResult({
  presentation,
}: {
  presentation: SummaryPresentation;
}) {
  if (presentation.sections.length === 0) {
    return null;
  }

  return (
          <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />

      <div className="divide-y divide-[#edf1ed]">
        {presentation.sections.map((section, index) => (
          <div
            key={`${section.label}-${index}`}
            className="grid grid-cols-[84px_minmax(0,1fr)] gap-4 px-4 py-3 sm:grid-cols-[100px_minmax(0,1fr)]"
          >
            <p className="text-[11px] font-medium leading-5 text-[#7d8b81]">
              {section.label}
            </p>

            <div className="min-w-0">
              <p className="break-words text-[12px] font-semibold leading-5 text-[#2c4135]">
                {section.primary}
              </p>

              {section.secondary && (
                <p className="mt-1 break-words text-[11px] leading-5 text-[#7d8b81]">
                  {section.secondary}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Customer360Result({
  presentation,
}: {
  presentation: Customer360Presentation;
}) {
  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
        <PresentationTitle title={presentation.title} />

        <div className="divide-y divide-[#edf1ed]">
          {presentation.sections.map((section, index) => (
            <div
              key={`${section.label}-${index}`}
              className="grid grid-cols-[84px_minmax(0,1fr)] gap-4 px-4 py-3 sm:grid-cols-[100px_minmax(0,1fr)]"
            >
              <p className="text-[11px] font-medium leading-5 text-[#7d8b81]">
                {section.label}
              </p>

              <div className="min-w-0">
                <p className="break-words text-[12px] font-semibold leading-5 text-[#2c4135]">
                  {section.primary}
                </p>

                {section.secondary && (
                  <p className="mt-1 break-words text-[11px] leading-5 text-[#7d8b81]">
                    {section.secondary}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {presentation.tables.map((table) => (
        table.rows.length > 0 ? (
          <TableResult
            key={table.title}
            presentation={{
              type: "table",
              title: table.title,
              columns: table.columns,
              rows: table.rows,
            }}
          />
        ) : (
          <div
            key={table.title}
            className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]"
          >
            <PresentationTitle title={table.title} />
            <p className="px-4 py-3 text-[11px] leading-5 text-[#7d8b81]">
              No records.
            </p>
          </div>
        )
      ))}
    </div>
  );
}

export function StructuredPresentation({
  presentation,
}: StructuredPresentationProps) {
  switch (presentation.type) {
    case "key_value":
      return (
        <KeyValueResult presentation={presentation} />
      );

    case "comparison":
      return (
        <ComparisonResult presentation={presentation} />
      );

    case "list":
      return (
        <ListResult presentation={presentation} />
      );

    case "table":
      return (
        <TableResult presentation={presentation} />
      );

    case "time_series":
      return (
        <Suspense
          fallback={(
            <div
              className="h-[340px] animate-pulse rounded-lg border border-[#dfe7e0] bg-white"
              role="status"
              aria-label="Loading chart"
            />
          )}
        >
          <TimeSeriesChart presentation={presentation} />
        </Suspense>
      );

    case "summary":
      return (
        <SummaryResult presentation={presentation} />
      );

    case "customer_360":
      return (
        <Customer360Result presentation={presentation} />
      );

    default:
      /*
       * This should be unreachable because ChatPresentation is a
       * discriminated union. Runtime API validation also discards
       * unknown presentation types.
       *
       * Returning null preserves the conversational text fallback.
       */
      return null;
  }
}