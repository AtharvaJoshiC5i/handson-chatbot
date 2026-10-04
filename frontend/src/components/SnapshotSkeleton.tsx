export function SnapshotSkeleton() {
  return (
    <div
      className="animate-pulse overflow-hidden rounded-xl border border-[#dfe7e0] bg-white"
      role="status"
      aria-label="Loading account snapshot"
    >
      <div className="border-b border-[#edf1ed] px-4 py-4">
        <div className="h-3 w-28 rounded bg-[#e8ede9]" />
        <div className="mt-3 h-4 w-48 rounded bg-[#e8ede9]" />
      </div>
      <div className="grid gap-4 p-4 sm:grid-cols-2">
        <div className="h-20 rounded-lg bg-[#f2f6f2]" />
        <div className="h-20 rounded-lg bg-[#f2f6f2]" />
      </div>
    </div>
  );
}
