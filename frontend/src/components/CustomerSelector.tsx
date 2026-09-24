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
    <div>
      <select
        id="customer-selector"
        value={customerId}
        onChange={(event) => onCustomerChange(event.target.value)}
        disabled={disabled}
        className="min-w-28 rounded-xl border border-[#d2e0de] bg-white px-3 py-2 text-xs font-bold text-[#36515b] outline-none transition hover:border-[#9fcac1] focus:border-[#42a99d] focus:ring-4 focus:ring-[#c9ece5] disabled:cursor-not-allowed disabled:bg-[#f1f5f4]"
      >
        {CUSTOMER_IDS.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>
    </div>
  );
}
