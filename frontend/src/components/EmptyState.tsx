import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
}

export default function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-card border border-dashed border-border-hover bg-surface p-16 text-center shadow-card">
      <span className="rounded-[10px] bg-blue-dim p-4 text-blue">{icon}</span>
      <div>
        <p className="text-[20px] font-semibold text-text-primary">{title}</p>
        <p className="mt-2 max-w-md text-[13px] text-text-secondary">{description}</p>
      </div>
    </div>
  );
}
