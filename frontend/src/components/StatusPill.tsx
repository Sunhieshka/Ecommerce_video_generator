import { cn } from "@/lib/utils";

interface StatusPillProps {
  status: string;
}

const statusMap: Record<string, string> = {
  completed: "bg-status-completed-bg text-status-completed-text border-status-completed-border",
  failed: "bg-status-failed-bg text-status-failed-text border-status-failed-border",
  running: "bg-status-running-bg text-status-running-text border-status-running-border",
  generating_video: "bg-status-running-bg text-status-running-text border-status-running-border",
  submitting_to_seedance: "bg-status-running-bg text-status-running-text border-status-running-border",
  prompt_generating: "bg-status-running-bg text-status-running-text border-status-running-border",
  queued: "bg-status-queued-bg text-status-queued-text border-status-queued-border",
};

export default function StatusPill({ status }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-pill border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.06em]",
        statusMap[status] ?? "bg-status-queued-bg text-status-queued-text border-status-queued-border",
      )}
    >
      {status.split("_").join(" ")}
    </span>
  );
}
