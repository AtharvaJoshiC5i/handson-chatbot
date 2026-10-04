interface ServiceSegmentProps {
  subscriptions: { plan_type: string; plan_name: string }[];
  value: string | null;
  onChange: (planType: string | null) => void;
}

export function ServiceSegment({
  subscriptions,
  value,
  onChange,
}: ServiceSegmentProps) {
  const types = [
    ...new Set(
      subscriptions.map((sub) => sub.plan_type),
    ),
  ];

  if (types.length <= 1) {
    return null;
  }

  return (
    <div
      className="inline-flex rounded-lg border border-[#dce5de] bg-[#f8faf8] p-0.5"
      role="tablist"
      aria-label="Service line"
    >
      <button
        type="button"
        role="tab"
        aria-selected={value === null}
        onClick={() => onChange(null)}
        className={[
          "rounded-md px-3 py-1.5 text-[10px] font-semibold transition-colors",
          value === null
            ? "bg-white text-[#264a38] shadow-sm"
            : "text-[#7d8b81] hover:text-[#41594a]",
        ].join(" ")}
      >
        All
      </button>

      {types.map((planType) => (
        <button
          key={planType}
          type="button"
          role="tab"
          aria-selected={value === planType}
          onClick={() => onChange(planType)}
          className={[
            "rounded-md px-3 py-1.5 text-[10px] font-semibold transition-colors",
            value === planType
              ? "bg-white text-[#264a38] shadow-sm"
              : "text-[#7d8b81] hover:text-[#41594a]",
          ].join(" ")}
        >
          {planType === "MOBILE" ? "Mobile" : planType === "FIBER" ? "Fiber" : planType}
        </button>
      ))}
    </div>
  );
}
