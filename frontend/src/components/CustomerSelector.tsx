interface CustomerSelectorProps {
  customerId: string;
  onCustomerChange: (customerId: string) => void;
  disabled?: boolean;
}

const CUSTOMER_IDS = ["CUST001", "CUST002", "CUST003", "CUST004", "CUST005"];

export function CustomerSelector({
  customerId,
  onCustomerChange,
  disabled = false,
}: CustomerSelectorProps) {
  return (
    <div className="flex flex-col gap-1">
      <label
        htmlFor="customer-selector"
        className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500"
      >
        Customer
      </label>

      <select
        id="customer-selector"
        value={customerId}
        onChange={(event) => onCustomerChange(event.target.value)}
        disabled={disabled}
        className="rounded-lg border border-slate-300 bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700 outline-none transition hover:border-slate-400 focus:border-teal-600 focus:ring-2 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-100"
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
