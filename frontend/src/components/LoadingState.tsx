export default function LoadingState({ label = "Loading job data..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-card border border-border bg-surface p-16 text-center shadow-card">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-blue/20 border-t-blue" />
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">{label}</p>
    </div>
  );
}
