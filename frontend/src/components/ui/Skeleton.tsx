import { cn } from "../../lib/cn";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-stone-200/70 motion-reduce:animate-none",
        className,
      )}
      aria-hidden="true"
    />
  );
}
