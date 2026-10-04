import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

const fieldShell = cn(
  "flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface",
  "px-3 shadow-sm shadow-stone-900/5 transition-[border-color,box-shadow] duration-150",
  "focus-within:border-brand/30 focus-within:ring-2 focus-within:ring-brand/15",
);

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export function SelectField({
  label,
  className,
  id,
  children,
  ...props
}: SelectFieldProps) {
  const selectId = id ?? "field-select";

  return (
    <label className="flex flex-col gap-1">
      {label ? (
        <span className="text-[10px] font-medium uppercase tracking-wide text-muted">
          {label}
        </span>
      ) : null}
      <div className={fieldShell}>
        <select
          id={selectId}
          className={cn(
            "min-w-0 flex-1 border-0 bg-transparent py-2 text-xs font-medium text-ink",
            "focus:outline-none disabled:opacity-50",
            className,
          )}
          {...props}
        >
          {children}
        </select>
      </div>
    </label>
  );
}

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function TextInput({ label, className, id, ...props }: TextInputProps) {
  const inputId = id ?? "field-input";

  return (
    <label className="flex flex-col gap-1">
      {label ? (
        <span className="text-[10px] font-medium uppercase tracking-wide text-muted">
          {label}
        </span>
      ) : null}
      <div className={fieldShell}>
        <input
          id={inputId}
          className={cn(
            "min-w-0 flex-1 border-0 bg-transparent py-2 text-xs text-ink",
            "placeholder:text-muted focus:outline-none disabled:opacity-50",
            className,
          )}
          {...props}
        />
      </div>
    </label>
  );
}

interface ComposerFieldProps {
  busy?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function ComposerField({
  busy = false,
  className,
  children,
}: ComposerFieldProps) {
  return (
    <div
      className={cn(
        fieldShell,
        "min-h-12 items-end gap-2 px-3 py-2",
        busy && "opacity-95",
        className,
      )}
      data-busy={busy ? "true" : undefined}
    >
      {children}
    </div>
  );
}
