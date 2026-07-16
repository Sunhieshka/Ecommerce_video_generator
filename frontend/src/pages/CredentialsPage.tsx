import { AlertCircle, KeyRound, Loader2 } from "lucide-react";
import { useState } from "react";

import { verifyCredentials } from "@/lib/api";
import { useCredentials } from "@/store/useCredentials";

export default function CredentialsPage() {
  const setCredentials = useCredentials((s) => s.setCredentials);
  const [arkApiKey, setArkApiKey] = useState("");
  const [byteplusAk, setByteplusAk] = useState("");
  const [byteplasSk, setByteplasSk] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleVerify() {
    if (!arkApiKey.trim() || !byteplusAk.trim() || !byteplasSk.trim()) {
      setError("All three credentials are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const creds = { arkApiKey: arkApiKey.trim(), byteplusAk: byteplusAk.trim(), byteplasSk: byteplasSk.trim() };
      await verifyCredentials(creds);
      setCredentials(creds);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-md rounded-card border border-border bg-surface p-8 shadow-card">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-[10px] bg-blue-dim p-2.5 text-blue">
            <KeyRound className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-[18px] font-semibold text-text-primary">BytePlus Credentials</h1>
            <p className="text-[12px] text-text-secondary">Enter your API keys to continue</p>
          </div>
        </div>

        <div className="space-y-4">
          <Field
            label="ARK API Key"
            placeholder="97f47e30-..."
            value={arkApiKey}
            onChange={setArkApiKey}
          />
          <Field
            label="BytePlus Access Key (AK)"
            placeholder="AKAP..."
            value={byteplusAk}
            onChange={setByteplusAk}
          />
          <Field
            label="BytePlus Secret Key (SK)"
            placeholder="TkRn..."
            value={byteplasSk}
            onChange={setByteplasSk}
            secret
          />
        </div>

        {error ? (
          <div className="mt-4 flex items-start gap-3 rounded-inner border border-status-failed-border bg-status-failed-bg px-4 py-3 text-[13px] text-status-failed-text">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        <button
          type="button"
          disabled={loading}
          onClick={handleVerify}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-semibold text-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Verifying...
            </>
          ) : (
            "Verify & Continue"
          )}
        </button>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  secret?: boolean;
}

function Field({ label, placeholder, value, onChange, secret }: FieldProps) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[12px] font-medium text-text-secondary">{label}</span>
      <input
        type={secret ? "password" : "text"}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-inner border border-border bg-bg px-3 py-2.5 text-[13px] text-ink outline-none transition focus:border-blue/40 focus:ring-[3px] focus:ring-blue-focus font-mono"
      />
    </label>
  );
}
