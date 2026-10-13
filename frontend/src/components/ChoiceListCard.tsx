import { ChevronRight } from "lucide-react";

import type { ChoiceListPresentation } from "../types/chat";
import { RichOptionCard } from "./RichOptionCard";

interface ChoiceListCardProps {
  presentation: ChoiceListPresentation;
  disabled?: boolean;
  onSelect?: (message: string) => void;
}

export function ChoiceListCard({
  presentation,
  disabled = false,
  onSelect,
}: ChoiceListCardProps) {
  const prompt = presentation.prompt?.trim();

  return (
    <div
      className="overflow-hidden rounded-xl border border-[#dce6de] bg-gradient-to-b from-white to-[#f8fbf8] shadow-[0_2px_12px_rgba(23,60,50,0.05)]"
      role="group"
      aria-label={presentation.title ?? "Choose an option"}
    >
      <div className="border-b border-[#e8ede9] px-4 py-3">
        <p className="text-[12px] font-semibold text-[#30493b]">
          {presentation.title ?? "Choose an option"}
        </p>
        {prompt && (
          <p className="mt-1 text-[12px] leading-relaxed text-[#5a6d62]">
            {prompt}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2 p-3 sm:flex-row sm:flex-wrap">
        {presentation.choices.map((choice) => (
          <RichOptionCard
            key={choice.message}
            option={choice}
            disabled={disabled}
            onSelect={(message) => onSelect?.(message)}
          />
        ))}
      </div>

      <p className="flex items-center gap-1 border-t border-[#edf1ed] px-4 py-2 text-[10px] text-[#96a198]">
        <ChevronRight size={12} aria-hidden="true" />
        Tap a card to continue
      </p>
    </div>
  );
}
