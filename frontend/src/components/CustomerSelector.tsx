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
          "h-8 min-w-[104px] appearance-none rounded-lg",
          "border border-[#e1e4e2] bg-white",
          "pl-3 pr-8",
          "text-[11px] font-medium text-[#3f4845]",
          "outline-none",
          "transition-colors duration-150",
          "hover:border-[#cbd0cd]",
          "focus:border-[#b7bdb9]",
          "focus:ring-2 focus:ring-[#202725]/5",
          "disabled:cursor-not-allowed",
          "disabled:bg-[#f6f7f6]",
          "disabled:text-[#9ba29f]",
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
          "-translate-y-1/2 text-[#858d8a]",
          disabled ? "opacity-40" : "",
        ].join(" ")}
      />
    </div>
  );
}
