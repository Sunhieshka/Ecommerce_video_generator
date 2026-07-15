import { AlertCircle, FileSpreadsheet, Sparkles, Upload } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "@/components/AppShell";
import { createJob } from "@/lib/api";
import type { AspectRatio, Resolution, VideoConfig } from "@/lib/types";

const RESOLUTION_OPTIONS: Resolution[] = ["480p", "720p", "1080p", "4k"];
const ASPECT_RATIO_OPTIONS: AspectRatio[] = ["16:9", "9:16", "1:1", "4:3", "3:4", "4:5"];

export default function CreateJobPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [config, setConfig] = useState<VideoConfig>({
    style: "cinematic",
    duration_seconds: 8,
    resolution: "1080p",
    aspect_ratio: "9:16",
    tone_override: null,
    sound_required: true,
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(() => Boolean(file) && !submitting, [file, submitting]);

  async function handleSubmit() {
    if (!file) {
      setError("Choose an Excel sheet before starting the batch.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await createJob(file, config, {
        referenceImages: [],
        referenceVideos: [],
        referenceVideoDurations: [],
        audioFiles: [],
      });
      navigate(`/jobs/${response.job_id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to create job");
      setSubmitting(false);
    }
  }

  return (
    <AppShell
      title="Excel Video Workspace"
      subtitle="Upload a workbook with product references, descriptions, optional human model imagery, and per-row video style and duration. The workbook is the only required input."
      aside={<WorkbookGuide />}
    >
      <section className="grid min-w-0 gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-card border border-border bg-surface p-6 shadow-card">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Input</p>
              <h2 className="mt-3 text-[20px] font-semibold text-text-primary">Create a new generation run</h2>
            </div>
            <div className="inline-flex items-center gap-1 rounded-pill border border-purple/20 bg-purple-dim px-3 py-1 text-[11px] font-medium text-purple">
              5 concurrent products
            </div>
          </div>

          <label className="flex cursor-pointer flex-col items-center justify-center rounded-inner border-[1.5px] border-dashed border-border-hover px-6 py-12 text-center transition-all hover:border-blue/40 hover:bg-blue/[0.03]">
            <div className="mb-2 rounded-[10px] bg-blue-dim p-3 text-blue">
              <Upload className="h-6 w-6" />
            </div>
            <p className="mt-2 text-[20px] font-semibold text-text-primary">Drop workbook or browse files</p>
            <p className="mt-2 max-w-lg text-[13px] text-text-secondary">
              Accepts `.xlsx` files with multiple product rows. Each valid row becomes one video job.
            </p>
            <input
              className="hidden"
              type="file"
              accept=".xlsx,.xls"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>

          <div className="mt-5 flex items-center gap-3 rounded-pill border border-border bg-surface px-4 py-3 text-[11px] text-text-secondary">
            <FileSpreadsheet className="h-4 w-4 text-purple" />
            <span>{file ? `${file.name} selected` : "No workbook selected yet"}</span>
          </div>

          <div className="mt-6 rounded-inner border border-border bg-bg px-4 py-4 text-[13px] leading-6 text-text-secondary">
            Additional reference image, video, and audio uploads have been removed. All product references, optional human model images, video style, and duration should come from the Excel workbook.
          </div>

          {error ? (
            <div className="mt-5 flex items-start gap-3 rounded-inner border border-status-failed-border bg-status-failed-bg px-4 py-4 text-[13px] text-status-failed-text">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : null}
        </div>

        <div className="rounded-card border border-border bg-surface p-6 shadow-card">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Video Generation</p>
              <h2 className="mt-3 text-[20px] font-semibold text-text-primary">Output controls</h2>
            </div>
            <Sparkles className="h-5 w-5 text-purple" />
          </div>

          <div className="mt-6 grid gap-3">
            <SelectField
              label="Resolution"
              value={config.resolution}
              onChange={(value) => setConfig((current) => ({ ...current, resolution: value as Resolution }))}
              options={RESOLUTION_OPTIONS}
            />
            <SelectField
              label="Aspect Ratio"
              value={config.aspect_ratio}
              onChange={(value) => setConfig((current) => ({ ...current, aspect_ratio: value as AspectRatio }))}
              options={ASPECT_RATIO_OPTIONS}
            />
            <p className="rounded-inner border border-border bg-bg px-4 py-4 text-[13px] leading-6 text-text-secondary">
              Video style and duration are read from the Excel sheet for each row. If a row is missing either field, the app falls back to the internal defaults.
            </p>
          </div>

          <button
            type="button"
            disabled={!canSubmit}
            onClick={handleSubmit}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-semibold text-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55"
          >
            {submitting ? "Creating batch..." : "Create Batch Job"}
          </button>
        </div>
      </section>
    </AppShell>
  );
}

function WorkbookGuide() {
  return (
    <div className="rounded-card border border-border bg-surface p-6 shadow-card">
      <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">Workbook Contract</p>
      <h3 className="mt-3 text-[20px] font-semibold text-text-primary">Expected columns</h3>
      <div className="mt-5 space-y-4 text-[13px] leading-6 text-text-secondary">
        <p>Accepted spreadsheet formats include your current layout and the earlier generic aliases.</p>
        <ul className="space-y-3">
          <li><span className="text-purple">Description:</span> `Product description` or `product_description`</li>
          <li><span className="text-purple">Product refs:</span> `Product reference image 1` to `Product reference image 4`</li>
          <li><span className="text-purple">Video style:</span> `Video Style` or `style`</li>
          <li><span className="text-purple">Duration:</span> `Duration` or `duration_seconds`</li>
          <li><span className="text-purple">Name:</span> optional, falls back to SKU or row id if missing</li>
          <li><span className="text-purple">Human model refs:</span> optional for the current parser</li>
          <li><span className="text-purple">SKU:</span> optional, defaults to row number if missing</li>
        </ul>
        <p className="rounded-inner border border-border bg-bg px-4 py-4 text-text-secondary">
          Multiple image references can be separated by commas, semicolons, or line breaks. The workbook is the only upload required in the current flow.
        </p>
      </div>
    </div>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  formatter?: (value: string) => string;
}

function SelectField({ label, value, options, onChange, formatter }: SelectFieldProps) {
  return (
    <label className="space-y-3">
      <span className="text-[12px] font-medium text-text-secondary">{label}</span>
      <select
        className="w-full rounded-inner border border-border bg-surface px-3 py-2.5 text-[13px] text-ink outline-none transition focus:border-blue/40 focus:ring-[3px] focus:ring-blue-focus"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {formatter ? formatter(option) : option}
          </option>
        ))}
      </select>
    </label>
  );
}
