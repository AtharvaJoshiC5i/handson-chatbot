import { ChevronDown } from "lucide-react";

interface CustomerSelectorProps {
  customerId: string;
  onCustomerChange: (customerId: string) => void;
  disabled?: boolean;
}

const CUSTOMER_IDS = [
  "CUST001",
  "CUST002",
  "CUST003",
  "CUST004",
  "CUST005",
  "CUST006",
  "CUST007",
];

export function CustomerSelector({
  customerId,
  onCustomerChange,
  disabled = false,
}: CustomerSelectorProps) {
  return (
    <div className="relative inline-flex">
      <select
        id="customer-selector"
        value={customerId}
        onChange={(event) => onCustomerChange(event.target.value)}
        disabled={disabled}
        aria-label="Select customer"
        className={[
          "h-9 min-w-[116px] appearance-none rounded-md",
          "border border-[#dce5de] bg-[#fbfcfb]",
          "pl-3 pr-8",
          "text-[11px] font-semibold tabular-nums text-[#30483c]",
          "outline-none",
          "transition-colors duration-150",
          "hover:border-[#b9cbbd] hover:bg-white",
          "focus:border-[#71927d]",
          "focus:ring-2 focus:ring-[#2f654f]/10",
          "disabled:cursor-not-allowed",
          "disabled:bg-[#f1f4f1]",
          "disabled:text-[#9ba89f]",
        ].join(" ")}
      >
        {CUSTOMER_IDS.map((id) => (
          <option key={id} value={id}>
            {id}
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
