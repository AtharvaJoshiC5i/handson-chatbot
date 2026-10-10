import { ChevronDown } from "lucide-react";

import type { DemoCustomer } from "../types/account";

interface CustomerSelectorProps {
  customerId: string;
  customers: DemoCustomer[];
  onCustomerChange: (customerId: string) => void;
  disabled?: boolean;
}

export function CustomerSelector({
  customerId,
  customers,
  onCustomerChange,
  disabled = false,
}: CustomerSelectorProps) {
  const options = customers.length > 0
    ? customers
    : [{ customer_id: customerId, name: customerId, phone_masked: "" }];

  return (
    <div className="relative inline-flex min-w-0 max-w-[min(100%,17.5rem)]">
      <select
        id="customer-selector"
        value={customerId}
        onChange={(event) => onCustomerChange(event.target.value)}
        disabled={disabled}
        aria-label="Select customer"
        className={[
          "h-9 w-full min-w-[160px] appearance-none truncate rounded-lg",
          "border border-[var(--color-line)] bg-white/90",
          "pl-3 pr-8",
          "text-[11px] font-semibold text-[var(--color-ink)]",
          "outline-none shadow-sm",
          "transition-colors duration-150",
          "hover:border-[#b9cbbd]",
          "focus:border-[#71927d]",
          "focus:ring-2 focus:ring-[#2f654f]/15",
          "disabled:cursor-not-allowed",
          "disabled:bg-[#f1f4f1]",
          "disabled:text-[#9ba89f]",
        ].join(" ")}
      >
        {options.map((customer) => (
          <option key={customer.customer_id} value={customer.customer_id}>
            {customer.name} · {customer.customer_id}
          </option>
        ))}
      </select>

      <ChevronDown
        size={13}
        strokeWidth={1.8}
        aria-hidden="true"
        className={[
          "pointer-events-none absolute right-2.5 top-1/2",
          "-translate-y-1/2 text-[#788a7e]",
          disabled ? "opacity-40" : "",
        ].join(" ")}
      />
    </div>
  );
}
