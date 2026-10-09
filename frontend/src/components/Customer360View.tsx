import {
  Bell,
  ChevronDown,
  CreditCard,
  Headphones,
  LayoutGrid,
  Mail,
  MapPin,
  Phone,
  Receipt,
  Smartphone,
  Wifi,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  Customer360Presentation,
  Customer360Table,
  SummarySection,
} from "../types/chat";

import { StructuredValue } from "./StructuredValue";
import { StatusChip } from "./StatusChip";
import { statusVariantForValue } from "../utils/statusChip";

interface Customer360ViewProps {
  presentation: Customer360Presentation;
  onEntitySelect?: (message: string) => void;
}

function findTable(
  tables: Customer360Table[],
  key: string,
): Customer360Table | undefined {
  return tables.find((table) =>
    table.title.toLowerCase().startsWith(key.toLowerCase()),
  );
}

function sectionByLabel(
  sections: SummarySection[],
  label: string,
): SummarySection | undefined {
  return sections.find((section) => section.label === label);
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return "?";
  }

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return `${parts[0][0] ?? ""}${parts[parts.length - 1][0] ?? ""}`.toUpperCase();
}

function attentionBullets(detail: string | null | undefined): string[] {
  if (!detail?.trim()) {
    return [];
  }

  const trimmed = detail.trim();
  if (trimmed.includes("\n")) {
    return trimmed.split("\n").map((line) => line.trim()).filter(Boolean);
  }

  const sentences = trimmed
    .split(/(?<=\.)\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 4);

  return sentences.length > 1 ? sentences : [trimmed];
}

function SummaryTile({
  label,
  icon: Icon,
  primary,
  secondary,
  onEntitySelect,
}: {
  label: string;
  icon: LucideIcon;
  primary: string;
  secondary?: string | null;
  onEntitySelect?: (message: string) => void;
}) {
  return (
    <div className="c360-tile">
      <span className="c360-tile-icon" aria-hidden>
        <Icon size={15} strokeWidth={2} />
      </span>
      <div className="c360-tile-body">
        <p className="c360-tile-label">{label}</p>
        <p className="c360-tile-primary">
          <StructuredValue
            label={label}
            value={primary}
            onEntitySelect={onEntitySelect}
          />
        </p>
        {secondary && (
          <p className="c360-tile-secondary">{secondary}</p>
        )}
      </div>
    </div>
  );
}

function CellValue({
  label,
  value,
  onEntitySelect,
}: {
  label: string;
  value: string;
  onEntitySelect?: (message: string) => void;
}) {
  const variant = statusVariantForValue(value);

  if (variant) {
    return <StatusChip variant={variant} label={value} />;
  }

  return (
    <StructuredValue
      label={label}
      value={value}
      onEntitySelect={onEntitySelect}
    />
  );
}

function FullDataTable({
  table,
  onEntitySelect,
}: {
  table: Customer360Table;
  onEntitySelect?: (message: string) => void;
}) {
  if (table.rows.length === 0) {
    return <p className="c360-empty">No records in this area.</p>;
  }

  return (
    <div className="c360-dense-table-wrap">
      <table className="c360-dense-table">
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column.key} scope="col">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {table.columns.map((column) => {
                const raw = row[column.key] ?? "—";
                return (
                  <td key={column.key}>
                    <CellValue
                      label={column.label}
                      value={raw}
                      onEntitySelect={onEntitySelect}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecordSection({
  table,
  onEntitySelect,
  defaultOpen = false,
}: {
  table: Customer360Table;
  onEntitySelect?: (message: string) => void;
  defaultOpen?: boolean;
}) {
  const recordCount = table.rows.length;
  const shortTitle = table.title.replace(/\s*\(\d+.*\)$/, "");

  return (
    <details className="c360-records-section" open={defaultOpen}>
      <summary className="c360-records-section-summary">
        <span>
          {shortTitle}
          <span className="c360-records-count">
            ({recordCount}{" "}
            {recordCount === 1 ? "record" : "records"})
          </span>
        </span>
        <ChevronDown
          size={14}
          className="c360-records-section-chevron"
          aria-hidden
        />
      </summary>
      <div className="c360-records-section-body">
        <FullDataTable table={table} onEntitySelect={onEntitySelect} />
      </div>
    </details>
  );
}

function ProfileDetailGrid({
  table,
  onEntitySelect,
}: {
  table: Customer360Table | undefined;
  onEntitySelect?: (message: string) => void;
}) {
  const row = table?.rows[0];
  if (!table || !row) {
    return null;
  }

  return (
    <dl className="c360-record-grid c360-profile-detail-grid">
      {table.columns.map((column) => {
        const raw = row[column.key] ?? "—";
        return (
          <div key={column.key} className="c360-profile-detail-item">
            <dt className="c360-field-label">{column.label}</dt>
            <dd className="c360-field-value">
              <CellValue
                label={column.label}
                value={raw}
                onEntitySelect={onEntitySelect}
              />
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

export function Customer360View({
  presentation,
  onEntitySelect,
}: Customer360ViewProps) {
  const customerTable = findTable(presentation.tables, "customer");
  const customerRow = customerTable?.rows[0];

  const accountSection = sectionByLabel(presentation.sections, "Account");
  const planSection = sectionByLabel(presentation.sections, "Plan");
  const usageSection = sectionByLabel(presentation.sections, "Usage");
  const billingSection = sectionByLabel(presentation.sections, "Billing");
  const paymentSection = sectionByLabel(presentation.sections, "Payment");
  const supportSection = sectionByLabel(presentation.sections, "Support");
  const devicesSection = sectionByLabel(presentation.sections, "Devices");
  const attentionSection = sectionByLabel(presentation.sections, "Attention");

  const detailTables = presentation.tables.filter(
    (table) => !table.title.toLowerCase().startsWith("customer"),
  );

  const totalDetailRows = detailTables.reduce(
    (sum, table) => sum + table.rows.length,
    0,
  );

  const name = customerRow?.name ?? "Customer";
  const accountStatus =
    customerRow?.account_status ?? accountSection?.primary ?? "—";
  const statusVariant = statusVariantForValue(accountStatus);

  const attentionNeedsAction =
    attentionSection &&
    !attentionSection.primary.toLowerCase().includes("nothing currently");

  const attentionItems = attentionBullets(attentionSection?.secondary);

  return (
    <div
      className="c360-widget"
      role="region"
      aria-labelledby="c360-widget-title"
    >
      <header className="c360-widget-header">
        <div className="c360-widget-header-main">
          <span className="c360-widget-mark" aria-hidden>
            <LayoutGrid size={18} strokeWidth={2} />
          </span>
          <div className="min-w-0">
            <p id="c360-widget-title" className="c360-widget-eyebrow">
              {presentation.title ?? "Account snapshot"}
            </p>
            <p className="c360-widget-sub">
              Summary first — expand below for every verified record
            </p>
          </div>
        </div>
      </header>

      <div className="c360-root">
        <section className="c360-card" aria-label="Profile">
          <div className="c360-profile">
            <div className="c360-avatar" aria-hidden>
              {initials(name)}
            </div>
            <div className="c360-profile-text">
              <p className="c360-profile-kicker">Account holder</p>
              <h2 className="c360-profile-name">{name}</h2>
              <p className="c360-profile-id">
                {customerRow?.customer_id ?? "Customer ID unavailable"}
              </p>
              <div className="c360-profile-status">
                {statusVariant ? (
                  <StatusChip variant={statusVariant} label={accountStatus} />
                ) : (
                  <span className="c360-profile-status-text">
                    {accountStatus}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="c360-contact-row">
            {customerRow?.email && (
              <a
                href={`mailto:${customerRow.email}`}
                className="c360-contact-chip"
              >
                <Mail size={13} aria-hidden />
                <span>{customerRow.email}</span>
              </a>
            )}
            {customerRow?.phone_number && (
              <span className="c360-contact-chip c360-contact-chip--muted">
                <Phone size={13} aria-hidden />
                <span>{customerRow.phone_number}</span>
              </span>
            )}
            {customerRow?.city && (
              <span className="c360-contact-chip c360-contact-chip--muted">
                <MapPin size={13} aria-hidden />
                <span>{customerRow.city}</span>
              </span>
            )}
          </div>

          {accountSection?.secondary && (
            <p className="c360-address">
              <MapPin size={14} className="shrink-0 text-[#8a968d]" aria-hidden />
              <span>{accountSection.secondary}</span>
            </p>
          )}

          {customerTable && (
            <details className="c360-profile-details">
              <summary className="c360-profile-details-summary">
                <span>Profile & registration details</span>
                <ChevronDown
                  size={14}
                  className="c360-records-section-chevron"
                  aria-hidden
                />
              </summary>
              <div className="c360-profile-details-body">
                <ProfileDetailGrid
                  table={customerTable}
                  onEntitySelect={onEntitySelect}
                />
              </div>
            </details>
          )}
        </section>

        {attentionNeedsAction && attentionSection && (
          <div className="c360-attention" role="status">
            <div className="c360-attention-icon" aria-hidden>
              <Bell size={16} strokeWidth={2} />
            </div>
            <div className="min-w-0">
              <p className="c360-attention-label">Needs attention</p>
              <p className="c360-attention-primary">
                {attentionSection.primary}
              </p>
              {attentionItems.length > 0 && (
                <ul className="c360-attention-list">
                  {attentionItems.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        <section className="c360-card" aria-label="Account overview">
          <div className="c360-overview-head">
            <h3 className="c360-overview-title">Overview</h3>
            <p className="c360-overview-hint">
              Key status across plan, usage, billing, and support
            </p>
          </div>
          <div className="c360-tile-grid">
            {planSection && (
              <SummaryTile
                label="Plan"
                icon={CreditCard}
                primary={planSection.primary}
                secondary={planSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
            {usageSection && (
              <SummaryTile
                label="Usage"
                icon={Wifi}
                primary={usageSection.primary}
                secondary={usageSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
            {billingSection && (
              <SummaryTile
                label="Billing"
                icon={Receipt}
                primary={billingSection.primary}
                secondary={billingSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
            {paymentSection && (
              <SummaryTile
                label="Payments"
                icon={CreditCard}
                primary={paymentSection.primary}
                secondary={paymentSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
            {supportSection && (
              <SummaryTile
                label="Support"
                icon={Headphones}
                primary={supportSection.primary}
                secondary={supportSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
            {devicesSection && (
              <SummaryTile
                label="Devices"
                icon={Smartphone}
                primary={devicesSection.primary}
                secondary={devicesSection.secondary}
                onEntitySelect={onEntitySelect}
              />
            )}
          </div>
        </section>

        {detailTables.length > 0 && (
          <details className="c360-records">
            <summary className="c360-records-summary">
              <span>
                Complete account records
                <span className="c360-records-count">
                  ({totalDetailRows} rows across {detailTables.length}{" "}
                  areas)
                </span>
              </span>
              <ChevronDown
                size={16}
                className="c360-records-chevron"
                aria-hidden
              />
            </summary>
            <div className="c360-records-body">
              {detailTables.map((table) => (
                <RecordSection
                  key={table.title}
                  table={table}
                  onEntitySelect={onEntitySelect}
                  defaultOpen={table.rows.length <= 3}
                />
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
