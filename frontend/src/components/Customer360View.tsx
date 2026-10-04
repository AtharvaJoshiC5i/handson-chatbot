import { ChevronDown } from "lucide-react";

import type {
  Customer360Presentation,
  Customer360Table,
  TablePresentation,
} from "../types/chat";

import { StructuredValue } from "./StructuredValue";
import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface Customer360ViewProps {
  presentation: Customer360Presentation;
  onEntitySelect?: (message: string) => void;
}

function findCustomerTable(
  tables: Customer360Table[],
): Customer360Table | undefined {
  return tables.find((table) =>
    table.title.toLowerCase().startsWith("customer"),
  );
}

function customerIdentityFromTable(
  table: Customer360Table | undefined,
): {
  name: string;
  customerId: string;
  email: string;
  phone: string;
  city: string;
  accountStatus: string;
} | null {
  if (!table || table.rows.length === 0) {
    return null;
  }

  const row = table.rows[0];

  return {
    name: row.name ?? "—",
    customerId: row.customer_id ?? "—",
    email: row.email ?? "—",
    phone: row.phone_number ?? "—",
    city: row.city ?? "—",
    accountStatus: row.account_status ?? "—",
  };
}

function CompactRecordGrid({
  table,
  onEntitySelect,
}: {
  table: Customer360Table;
  onEntitySelect?: (message: string) => void;
}) {
  const row = table.rows[0];

  return (
    <dl className="grid gap-x-4 gap-y-2 sm:grid-cols-2">
      {table.columns.map((column) => {
        const raw = row[column.key] ?? "—";
        const variant = statusVariantForValue(raw);

        return (
          <div key={column.key} className="min-w-0">
            <dt className="text-[10px] font-medium uppercase tracking-wide text-[#8a968d]">
              {column.label}
            </dt>
            <dd className="mt-0.5 break-words text-[12px] leading-5 text-[#2c4135]">
              {variant ? (
                <StatusChip variant={variant} label={raw} />
              ) : (
                <StructuredValue
                  label={column.label}
                  value={raw}
                  onEntitySelect={onEntitySelect}
                />
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

function DenseTable({
  presentation,
  onEntitySelect,
}: {
  presentation: TablePresentation;
  onEntitySelect?: (message: string) => void;
}) {
  if (presentation.columns.length === 0 || presentation.rows.length === 0) {
    return null;
  }

  return (
    <div className="max-h-56 overflow-auto rounded-md border border-[#e8ede9]">
      <table className="w-full min-w-[420px] border-collapse text-left">
        <thead className="sticky top-0 z-[1] bg-[#f6f8f6]">
          <tr className="border-b border-[#e5ebe6]">
            {presentation.columns.map((column) => (
              <th
                key={column.key}
                className="whitespace-nowrap px-3 py-2 text-[10px] font-semibold text-[#65766a]"
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
                  className="px-3 py-2 text-[11px] leading-5 text-[#34483b]"
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
  );
}

export function Customer360View({
  presentation,
  onEntitySelect,
}: Customer360ViewProps) {
  const customerTable = findCustomerTable(presentation.tables);
  const identity = customerIdentityFromTable(customerTable);

  const recordTables = presentation.tables.filter((table) => {
    if (table.rows.length === 0) {
      return false;
    }

    if (
      identity &&
      table.title.toLowerCase().startsWith("customer") &&
      table.rows.length === 1
    ) {
      return false;
    }

    return true;
  });

  const recordCount = recordTables.length;

  return (
    <div className="structured-export space-y-3">
      <div className="overflow-hidden rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
        {identity && (
          <div className="border-b border-[#edf1ed] px-4 py-3">
            <p className="text-[15px] font-semibold tracking-tight text-[#1a3328]">
              {identity.name}
            </p>
            <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-[#7d8b81]">
              <span className="font-medium text-[#52665a]">
                {identity.customerId}
              </span>
              <span className="text-[#c5cec7]" aria-hidden="true">·</span>
              <span>{identity.email}</span>
              <span className="text-[#c5cec7]" aria-hidden="true">·</span>
              <span>{identity.phone}</span>
              <span className="text-[#c5cec7]" aria-hidden="true">·</span>
              <span>{identity.city}</span>
              {identity.accountStatus !== "—" && (
                <>
                  <span className="text-[#c5cec7]" aria-hidden="true">·</span>
                  {(() => {
                    const variant = statusVariantForValue(
                      identity.accountStatus,
                    );

                    return variant
                      ? (
                          <StatusChip
                            variant={variant}
                            label={identity.accountStatus}
                          />
                        )
                      : <span>{identity.accountStatus}</span>;
                  })()}
                </>
              )}
            </p>
          </div>
        )}

        {presentation.sections.length > 0 && (
          <div className="grid gap-px bg-[#edf1ed] sm:grid-cols-2">
            {presentation.sections.map((section, index) => (
              <div
                key={`${section.label}-${index}`}
                className="bg-white px-4 py-2.5"
              >
                <p className="text-[10px] font-medium uppercase tracking-wide text-[#8a968d]">
                  {section.label}
                </p>
                <p className="mt-1 break-words text-[12px] font-semibold leading-5 text-[#2c4135]">
                  <StructuredValue
                    label={section.label}
                    value={section.primary}
                    onEntitySelect={onEntitySelect}
                  />
                </p>
                {section.secondary && (
                  <p className="mt-0.5 break-words text-[11px] leading-5 text-[#7d8b81]">
                    {section.secondary}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {recordCount > 0 && (
        <details className="group rounded-lg border border-[#dfe7e0] bg-white shadow-[0_1px_4px_rgba(23,60,50,0.03)]">
          <summary
            className={[
              "flex cursor-pointer list-none items-center justify-between gap-3",
              "px-4 py-3 text-[12px] font-semibold text-[#2c4135]",
              "marker:content-none [&::-webkit-details-marker]:hidden",
              "hover:bg-[#fafbfa]",
            ].join(" ")}
          >
            <span>
              Supporting records
              <span className="ml-1.5 font-normal text-[#7d8b81]">
                ({recordCount})
              </span>
            </span>
            <ChevronDown
              size={16}
              className="shrink-0 text-[#8a968d] transition group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>

          <div className="divide-y divide-[#edf1ed] border-t border-[#edf1ed]">
            {recordTables.map((table) => (
              <details
                key={table.title}
                className="group/section"
              >
                <summary
                  className={[
                    "flex cursor-pointer list-none items-center justify-between gap-3",
                    "px-4 py-2.5 text-[11px] font-semibold text-[#41594a]",
                    "marker:content-none [&::-webkit-details-marker]:hidden",
                    "hover:bg-[#fafbfa]",
                  ].join(" ")}
                >
                  <span>{table.title}</span>
                  <ChevronDown
                    size={14}
                    className="shrink-0 text-[#8a968d] transition group-open/section:rotate-180"
                    aria-hidden="true"
                  />
                </summary>
                <div className="border-t border-[#edf1ed] bg-[#fafbfa] px-4 py-3">
                  {table.rows.length === 1 ? (
                    <CompactRecordGrid
                      table={table}
                      onEntitySelect={onEntitySelect}
                    />
                  ) : (
                    <DenseTable
                      onEntitySelect={onEntitySelect}
                      presentation={{
                        type: "table",
                        title: table.title,
                        columns: table.columns,
                        rows: table.rows,
                      }}
                    />
                  )}
                </div>
              </details>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
