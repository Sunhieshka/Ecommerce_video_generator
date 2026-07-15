import { ArrowRight, RefreshCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppShell from "@/components/AppShell";
import LoadingState from "@/components/LoadingState";
import MetricCard from "@/components/MetricCard";
import ProductTable from "@/components/ProductTable";
import { retryFailed } from "@/lib/api";
import { useJobStore } from "@/store/useJobStore";

export default function JobMonitorPage() {
  const { jobId } = useParams();
  const { job, products, error, loadJob, clear } = useJobStore();
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (!jobId) {
      return;
    }
    loadJob(jobId);
    const timer = window.setInterval(() => loadJob(jobId), 2000);
    return () => {
      window.clearInterval(timer);
      clear();
    };
  }, [clear, jobId, loadJob]);

  const runningCount = useMemo(() => {
    if (!job) {
      return 0;
    }
    return job.counts.prompt_generating + job.counts.submitting_to_seedance + job.counts.generating_video;
  }, [job]);

  async function handleRetry() {
    if (!jobId) {
      return;
    }
    setRetrying(true);
    await retryFailed(jobId);
    await loadJob(jobId);
    setRetrying(false);
  }

  return (
    <AppShell
      title="Generation monitor"
      subtitle="Track prompt creation, provider submission, and per-product completion in one place. The queue refreshes automatically while your batch is running."
      aside={job ? <JobAside fileName={job.original_filename} /> : null}
    >
      {!job ? (
        <LoadingState label={error ?? "Loading job data..."} />
      ) : (
        <section className="min-w-0 space-y-6">
          <div className="rounded-card border border-border bg-surface p-6 shadow-card">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Input</p>
                <h2 className="mt-3 text-[20px] font-semibold text-text-primary">{`Job ${job.id.slice(0, 8)}`}</h2>
                <p className="mt-3 max-w-2xl text-[13px] text-text-secondary">
                  {error ? error : "Live status, prompt content, and product outcomes update every two seconds."}
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleRetry}
                  disabled={retrying || job.counts.failed === 0}
                  className="inline-flex items-center gap-2 rounded-inner border border-border bg-transparent px-4 py-2.5 text-[13px] font-medium text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-55"
                >
                  <RefreshCcw className="h-4 w-4" />
                  {retrying ? "Retrying..." : "Retry Failed"}
                </button>
                {jobId ? (
                  <Link
                    to={`/jobs/${jobId}/results`}
                    className="inline-flex items-center gap-2 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-semibold text-bg transition-opacity hover:opacity-90"
                  >
                    Open Results
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                ) : null}
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard label="Queued" value={job.counts.queued} />
            <MetricCard label="Running" value={runningCount} tone="highlight" />
            <MetricCard label="Completed" value={job.counts.completed} />
            <MetricCard label="Failed" value={job.counts.failed} />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <MetricCard label="Output" value={`${job.resolution} · ${job.aspect_ratio}`} />
            <MetricCard label="Status" value={job.status} />
          </div>

          <ProductTable products={products} />
        </section>
      )}
    </AppShell>
  );
}

function JobAside({ fileName }: { fileName: string }) {
  return (
    <div className="rounded-card border border-border bg-surface p-5 shadow-card">
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Current Workbook</p>
      <h3 className="mt-3 break-words text-[18px] font-semibold leading-6 text-text-primary">{fileName}</h3>
    </div>
  );
}
