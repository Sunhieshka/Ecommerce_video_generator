interface MetricCardProps {
  label: string;
  value: string | number;
  tone?: "default" | "highlight";
}

export default function MetricCard({ label, value, tone = "default" }: MetricCardProps) {
  const stringValue = String(value);
  const isLongValue = stringValue.length > 14;

  return (
    <div
      className={
        tone === "highlight"
          ? "rounded-card border border-blue-border bg-blue/[0.04] p-6 shadow-card"
          : "rounded-card border border-border bg-surface p-6 shadow-card"
      }
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">{label}</p>
      <p
        className={`mt-3 break-words font-semibold text-text-primary ${
          isLongValue ? "text-[18px] leading-7" : "text-[24px] leading-8"
        }`}
      >
        {stringValue}
      </p>
    </div>
  );
}
