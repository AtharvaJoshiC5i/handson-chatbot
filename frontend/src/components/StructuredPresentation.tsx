import { lazy, Suspense } from "react";

import type {
  ChatPresentation,
  ComparisonPresentation,
  KeyValuePresentation,
  ListPresentation,
  SummaryPresentation,
  TablePresentation,
} from "../types/chat";
import { parseUsageFromKeyValue } from "../utils/parseUsageMeter";

import {
  BillListCards,
  isBillTablePresentation,
} from "./BillListCards";
import { ComparisonHero } from "./ComparisonHero";
import {
  isPaymentListPresentation,
  PaymentRowList,
} from "./PaymentRowList";
import { StructuredValue } from "./StructuredValue";
import {
  isSubscriptionListPresentation,
  SubscriptionInventoryCards,
} from "./SubscriptionInventoryCards";
import {
  isTicketTimelinePresentation,
  TicketTimeline,
} from "./TicketTimeline";
import { UsageMeter } from "./UsageMeter";
import { Customer360View } from "./Customer360View";
import { chartPresentationShell } from "../lib/presentationStyles";

const TimeSeriesChart = lazy(() =>
  import("./TimeSeriesChart").then((module) => ({
    default: module.TimeSeriesChart,
  })),
);

interface StructuredPresentationProps {
  presentation: ChatPresentation;
  onEntitySelect?: (message: string) => void;
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
  onEntitySelect,
}: {
  presentation: KeyValuePresentation;
  onEntitySelect?: (message: string) => void;
}) {
  if (presentation.items.length === 0) {
    return null;
  }

  const usage = parseUsageFromKeyValue(
    presentation.items,
  );

  return (
    <div className="structured-export space-y-3">
      {usage && (
        <UsageMeter
          usedGb={usage.usedGb}
          limitGb={usage.limitGb}
          isUnlimited={usage.isUnlimited}
        />
      )}

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
                <StructuredValue
                  label={item.label}
                  value={item.value}
                  onEntitySelect={onEntitySelect}
                />
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

function ComparisonResult({
  presentation,
  onEntitySelect,
}: {
  presentation: ComparisonPresentation;
  onEntitySelect?: (message: string) => void;
}) {
  if (
    presentation.columns.length === 0 ||
    presentation.rows.length === 0
  ) {
    return null;
  }

  return (
    <div className="structured-export overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
      <PresentationTitle title={presentation.title} />
      <div className="px-4 pt-3">
        <ComparisonHero presentation={presentation} />
      </div>

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
                    <StructuredValue
                      label={row.label}
                      value={row.values[column.key] ?? "—"}
                      onEntitySelect={onEntitySelect}
                    />
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
  onEntitySelect,
}: {
  presentation: ListPresentation;
  onEntitySelect?: (message: string) => void;
}) {
  if (presentation.items.length === 0) {
    return null;
  }

  if (isTicketTimelinePresentation(presentation)) {
    return (
      <div className="structured-export overflow-hidden rounded-lg border border-[#dfe7e0] bg-white p-4 shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
        <PresentationTitle title={presentation.title} />
        <TicketTimeline presentation={presentation} />
      </div>
    );
  }

  if (isPaymentListPresentation(presentation)) {
    return (
      <div className="structured-export overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
        <PresentationTitle title={presentation.title} />
        <div className="space-y-2 p-4">
          <PaymentRowList presentation={presentation} />
        </div>
      </div>
    );
  }

  if (isSubscriptionListPresentation(presentation)) {
    return (
      <div className="structured-export space-y-3">
        <PresentationTitle title={presentation.title} />
        <SubscriptionInventoryCards presentation={presentation} />
      </div>
    );
  }

  return (
    <div className="structured-export overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
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
              <StructuredValue
                label={item.label}
                value={item.value}
                onEntitySelect={onEntitySelect}
              />
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TableResult({
  presentation,
  onEntitySelect,
}: {
  presentation: TablePresentation;
  onEntitySelect?: (message: string) => void;
}) {
  if (
    presentation.columns.length === 0 ||
    presentation.rows.length === 0
  ) {
    return null;
  }

  const showBillCards = isBillTablePresentation(
    presentation,
  );

  return (
    <div className="structured-export space-y-3">
      {showBillCards && (
        <BillListCards
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
      )}

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
                    <StructuredValue
                      label={column.label}
                      value={row[column.key] ?? "—"}
                      onEntitySelect={onEntitySelect}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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

export function StructuredPresentation({
  presentation,
  onEntitySelect,
}: StructuredPresentationProps) {
  switch (presentation.type) {
    case "key_value":
      return (
        <KeyValueResult
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
      );

    case "comparison":
      return (
        <ComparisonResult
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
      );

    case "list":
      return (
        <ListResult
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
      );

    case "table":
      return (
        <TableResult
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
      );

    case "time_series":
      return (
        <Suspense
          fallback={(
            <div
              className={`h-[340px] animate-pulse ${chartPresentationShell}`}
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
        <Customer360View
          presentation={presentation}
          onEntitySelect={onEntitySelect}
        />
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