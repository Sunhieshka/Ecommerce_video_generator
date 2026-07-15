import { Film, Sparkles, Workflow } from "lucide-react";
import { Link } from "react-router-dom";
import type { PropsWithChildren, ReactNode } from "react";

interface AppShellProps extends PropsWithChildren {
  title: string;
  subtitle: string;
  aside?: ReactNode;
}

export default function AppShell({ title, subtitle, aside, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-bg px-6 py-8 font-sans text-text-primary">
      <div className="mx-auto max-w-[1240px]">
        <header className="mb-8">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="inline-flex items-center gap-1.5 rounded-pill border border-blue-border bg-blue-dim px-3 py-1 text-[11px] font-medium tracking-[0.04em] text-blue">
              <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] shadow-[0_0_0_2px_rgba(34,197,94,0.25)]" />
              BytePlus Video API
            </div>
          </div>
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Creative Production Tool</p>
              <div>
                <h1 className="text-[28px] font-semibold tracking-[-0.5px] text-ink">
                  {renderGradientTitle(title)}
                </h1>
                <p className="mt-1 max-w-3xl text-[13px] text-text-secondary">{subtitle}</p>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <StatTile icon={<Sparkles className="h-4 w-4" />} label="LLM Model" value="seed-2-0-pro-260328" />
              <StatTile icon={<Film className="h-4 w-4" />} label="Seedance" value="dreamina-seedance-2-0-260128" />
              <StatTile icon={<Workflow className="h-4 w-4" />} label="Batch Limit" value="5 products" />
            </div>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-semibold text-bg transition-opacity hover:opacity-90"
            >
              Create New Job
            </Link>
          </div>
        </header>

        <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_200px]">
          <main className="min-w-0 space-y-6">{children}</main>
          <aside className="min-w-0 space-y-6">{aside}</aside>
        </div>
      </div>
    </div>
  );
}

function StatTile({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-card border border-border bg-surface px-3 py-2.5 shadow-card">
      <div className="flex items-center gap-1.5 text-purple">
        {icon}
        <span className="text-[9px] font-semibold uppercase tracking-[0.08em] text-text-tertiary">{label}</span>
      </div>
      <p className="mt-2 break-words text-[12px] font-medium leading-5 text-text-primary">{value}</p>
    </div>
  );
}

function renderGradientTitle(title: string) {
  const words = title.split(" ");
  if (words.length < 2) {
    return <span className="bg-brand bg-clip-text text-transparent">{title}</span>;
  }

  const accent = words[words.length - 1];
  const base = words.slice(0, -1).join(" ");
  return (
    <>
      {base} <span className="bg-brand bg-clip-text text-transparent">{accent}</span>
    </>
  );
}
