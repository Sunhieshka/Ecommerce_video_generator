import { Download, ExternalLink, PackageSearch, RefreshCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppShell from "@/components/AppShell";
import EmptyState from "@/components/EmptyState";
import LoadingState from "@/components/LoadingState";
import StatusPill from "@/components/StatusPill";
import { regenerateProduct } from "@/lib/api";
import type { ProductItem } from "@/lib/types";
import { useCredentials } from "@/store/useCredentials";
import { useJobStore } from "@/store/useJobStore";

export default function ResultsPage() {
  const { jobId } = useParams();
  const credentials = useCredentials((s) => s.credentials);
  const { job, products, loadJob, clear } = useJobStore();
  const totalEstimatedCost = useMemo(
    () => products.reduce((sum, product) => sum + (product.estimated_price_usd ?? 0), 0),
    [products],
  );
  const productsWithEstimatedCost = useMemo(
    () => products.filter((product) => product.estimated_price_usd !== null).length,
    [products],
  );

  useEffect(() => {
    if (!jobId) {
      return;
    }
    loadJob(jobId, credentials);
    const timer = window.setInterval(() => loadJob(jobId, credentials), 3000);
    return () => {
      window.clearInterval(timer);
      clear();
    };
  }, [clear, jobId, loadJob, credentials]);

  return (
    <AppShell
      title="Batch outputs"
      subtitle="Review prompts, inspect per-product results, and download generated artifacts or provider outputs for the selected batch."
      aside={
        <div className="space-y-4">
          <div className="rounded-card border border-border bg-surface p-6 shadow-card">
            <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Results</p>
            <h3 className="mt-3 text-[20px] font-semibold text-text-primary">{job ? job.original_filename : "Loading..."}</h3>
            <p className="mt-4 text-[13px] text-text-secondary">
              {job ? `${job.counts.completed} completed · ${job.counts.failed} failed` : "Fetching job summary..."}
            </p>
            {jobId ? (
              <Link
                to={`/jobs/${jobId}`}
                className="mt-5 inline-flex rounded-inner border border-border bg-transparent px-4 py-2.5 text-[13px] font-medium text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
              >
                Back to Monitor
              </Link>
            ) : null}
          </div>
          <GenerationCostCard totalEstimatedCost={totalEstimatedCost} productsWithEstimatedCost={productsWithEstimatedCost} />
        </div>
      }
    >
      {!job ? (
        <LoadingState label="Loading batch outputs..." />
      ) : products.length === 0 ? (
        <EmptyState
          icon={<PackageSearch className="h-6 w-6" />}
          title="No results yet"
          description="Products will appear here once prompt generation and video rendering complete for this batch."
        />
      ) : (
        <section className="grid min-w-0 gap-6 xl:grid-cols-2">
          {products.map((product) => (
            <EditableResultCard
              key={product.id}
              jobId={jobId!}
              product={product}
              onRegenerated={() => loadJob(jobId!, credentials)}
            />
          ))}
        </section>
      )}
    </AppShell>
  );
}

function GenerationCostCard({
  totalEstimatedCost,
  productsWithEstimatedCost,
}: {
  totalEstimatedCost: number;
  productsWithEstimatedCost: number;
}) {
  return (
    <div className="rounded-card border border-border bg-surface p-6 shadow-card">
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Total Cost</p>
      <p className="mt-3 text-[24px] font-semibold text-text-primary">
        {productsWithEstimatedCost > 0 ? formatUsd(totalEstimatedCost) : "Pending"}
      </p>
      <p className="mt-2 text-[13px] text-text-secondary">
        {productsWithEstimatedCost > 0
          ? `Based on ${productsWithEstimatedCost} generated video${productsWithEstimatedCost === 1 ? "" : "s"} with pricing data.`
          : "Cost will appear when generated videos report pricing data."}
      </p>
    </div>
  );
}

function EditableResultCard({
  jobId,
  product,
  onRegenerated,
}: {
  jobId: string;
  product: ProductItem;
  onRegenerated: () => Promise<void> | void;
}) {
  const credentials = useCredentials((s) => s.credentials);
  const [prompt, setPrompt] = useState(product.generated_prompt ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setPrompt(product.generated_prompt ?? "");
  }, [product.generated_prompt, product.id]);

  async function handleRegenerate() {
    if (!prompt.trim()) {
      setMessage("Enter a prompt before regenerating this result.");
      return;
    }

    setSubmitting(true);
    setMessage(null);
    try {
      await regenerateProduct(jobId, product.id, prompt.trim(), credentials);
      await onRegenerated();
      setMessage("Regeneration started. This result card will refresh with the new output.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to regenerate this product.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-card border border-border bg-surface shadow-card">
      <div className="h-[3px] bg-brand-h" />
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Result {product.row_number}</p>
            <h2 className="mt-3 text-[20px] font-semibold text-text-primary">{product.product_name}</h2>
            <p className="mt-2 font-mono text-[11px] text-purple-muted">{product.sku}</p>
          </div>
          <StatusPill status={product.status} />
        </div>

        <p className="mt-5 text-[13px] leading-6 text-text-secondary">{product.product_description}</p>

        <VideoPreview jobId={jobId} product={product} />
        <UsageAndPrice product={product} />

        <div className="mt-5 overflow-hidden rounded-card border border-blue/30 bg-surface">
          <div className="border-b border-border px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">
            Editable Prompt
          </div>
          <div className="px-4 py-4">
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="min-h-[180px] w-full rounded-inner border border-border bg-bg px-3 py-3 font-mono text-[12px] leading-6 text-text-secondary outline-none transition focus:border-blue/40 focus:ring-[3px] focus:ring-blue-focus"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleRegenerate}
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-semibold text-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55"
          >
            <RefreshCcw className="h-4 w-4" />
            {submitting ? "Generating..." : "Generate Again"}
          </button>
          {product.output_path ? (
            <a
              href={`/api/jobs/${jobId}/download/${product.id}`}
              className="inline-flex items-center gap-2 rounded-inner border border-border bg-transparent px-4 py-2.5 text-[11px] font-medium text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
            >
              <Download className="h-4 w-4" />
              Download Artifact
            </a>
          ) : null}
          {product.download_url ? (
            <a
              href={product.download_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-inner border border-border bg-transparent px-4 py-2.5 text-[11px] font-medium text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
            >
              <ExternalLink className="h-4 w-4" />
              Open Provider Output
            </a>
          ) : null}
        </div>

        {message ? (
          <div className="mt-4 rounded-inner border border-blue-border bg-blue/[0.04] px-4 py-3 text-[13px] text-text-secondary">
            {message}
          </div>
        ) : null}

        {product.error_message ? (
          <div className="mt-5 rounded-inner border border-status-failed-border bg-status-failed-bg px-4 py-4 text-[13px] text-status-failed-text">
            {product.error_message}
          </div>
        ) : null}
      </div>
    </article>
  );
}

function UsageAndPrice({ product }: { product: ProductItem }) {
  const hasUsage =
    product.token_consumption !== null ||
    product.estimated_price_usd !== null;

  if (!hasUsage) {
    return null;
  }

  return (
    <div className="mt-5 rounded-card border border-border bg-bg p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Usage & Price</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="rounded-inner border border-border bg-surface px-3 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Token Consumption</p>
          <p className="mt-2 text-[16px] font-semibold text-text-primary">
            {product.token_consumption !== null ? formatNumber(product.token_consumption) : "Pending"}
          </p>
        </div>
        <div className="rounded-inner border border-border bg-surface px-3 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Cost Per Video</p>
          <p className="mt-2 text-[16px] font-semibold text-text-primary">
            {product.estimated_price_usd !== null ? `$${product.estimated_price_usd.toFixed(6)}` : "Pending"}
          </p>
        </div>
      </div>
    </div>
  );
}

function VideoPreview({
  jobId,
  product,
}: {
  jobId: string;
  product: ProductItem;
}) {
  const previewUrl = getVideoPreviewUrl(jobId, product);

  if (!previewUrl) {
    return (
      <div className="mt-5 rounded-card border border-dashed border-border-hover bg-bg p-5">
        <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Video Preview</p>
        <p className="mt-3 text-[13px] text-text-secondary">
          {product.status === "completed"
            ? "Video output is completed, but no playable preview URL is available yet."
            : "Preview will appear here when a playable video output is available."}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-5 rounded-card border border-border bg-surface p-4">
      <div className="overflow-hidden rounded-inner border border-border bg-ink">
        <video
          className="video-player aspect-[9/16] w-full object-contain md:aspect-video"
          controls
          preload="metadata"
          playsInline
          src={previewUrl}
        >
          Your browser does not support video playback.
        </video>
      </div>
    </div>
  );
}

function getVideoPreviewUrl(
  jobId: string,
  product: {
    id: string;
    output_path: string | null;
    download_url: string | null;
  },
): string | null {
  if (product.download_url && isLikelyVideoUrl(product.download_url)) {
    return product.download_url;
  }

  if (product.output_path && isLikelyVideoUrl(product.output_path)) {
    return `/api/jobs/${jobId}/download/${product.id}`;
  }

  return null;
}

function isLikelyVideoUrl(value: string): boolean {
  const videoExtensions = [".mp4", ".mov", ".webm", ".m4v", ".avi"];

  try {
    const parsed = value.startsWith("http://") || value.startsWith("https://") ? new URL(value) : null;
    const pathname = parsed ? parsed.pathname.toLowerCase() : value.toLowerCase();
    return videoExtensions.some((extension) => pathname.endsWith(extension));
  } catch {
    const normalized = value.toLowerCase();
    return videoExtensions.some((extension) => normalized.endsWith(extension));
  }
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 6,
  }).format(value);
}
