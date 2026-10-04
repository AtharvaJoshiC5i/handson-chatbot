import type { AccountSnapshot } from "../../types/account";
import {
  buildWelcomeLead,
  greetingForLocalHour,
  personalAssistantTagline,
} from "../../utils/welcomePersonalization";
import { AccountIdentityMeta } from "./AccountIdentityMeta";
import { AccountServiceLocation } from "./AccountServiceLocation";

interface WelcomePersonalHeroProps {
  displayName: string;
  snapshot: AccountSnapshot | null;
  useTimeGreeting?: boolean;
}

export function WelcomePersonalHero({
  displayName,
  snapshot,
  useTimeGreeting = true,
}: WelcomePersonalHeroProps) {
  const firstName = displayName.split(" ")[0];
  const heading = useTimeGreeting
    ? `${greetingForLocalHour()}, ${firstName}`
    : displayName;

  return (
    <header className="welcome-personal-hero">
      {snapshot && <AccountIdentityMeta snapshot={snapshot} />}

      <p className="welcome-personal-tagline">
        {personalAssistantTagline(firstName)}
      </p>

      <h1 className="welcome-title welcome-title--minimal">{heading}</h1>

      {snapshot && (
        <p className="welcome-lead welcome-lead--minimal">
          {buildWelcomeLead(snapshot)}
        </p>
      )}

      {snapshot && <AccountServiceLocation snapshot={snapshot} />}
    </header>
  );
}
