import { MapPin } from "lucide-react";

import type { AccountSnapshot } from "../../types/account";
import { serviceLocationLine } from "../../utils/welcomePersonalization";

interface AccountServiceLocationProps {
  snapshot: AccountSnapshot;
}

export function AccountServiceLocation({
  snapshot,
}: AccountServiceLocationProps) {
  const locationLine = serviceLocationLine(snapshot);

  if (!locationLine) {
    return null;
  }

  return (
    <p className="welcome-location flex items-start gap-1.5">
      <MapPin
        size={12}
        className="mt-0.5 shrink-0 text-[#9aa89f]"
        aria-hidden="true"
      />
      <span>{locationLine}</span>
    </p>
  );
}
