import { useState } from "react";
import { verifyLabel, submitDecision } from "../services/api";
import type { ApplicationManifest, VerifyResponse, AgentDecision } from "../services/types";
import StatusBadge from "../components/StatusBadge";
import ChecklistRow from "../components/ChecklistRow";
import LatencyClock from "../components/LatencyClock";

const EMPTY_MANIFEST: ApplicationManifest = {
  application_id: "",
  brand_name: "",
  class_type: "",
  alcohol_by_volume: "",
  net_contents: "",
};

export default function ReviewPage() {
  const [manifest, setManifest] = useState<ApplicationManifest>(EMPTY_MANIFEST);
  const [file, setFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);

  function handleFieldChange(field: keyof ApplicationManifest, value: string) {
    setManifest((prev) => ({ ...prev, [field]: value }));
  }

  function handleFileChange(selected: File | null) {
    setFile(selected);
    setImagePreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please select a label image to verify.");
      return;
    }
    setError(null);
    setDecisionMessage(null);
    setIsLoading(true);
    try {
      const response = await verifyLabel(file, manifest);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDecision(decision: AgentDecision) {
    if (!result) return;
    try {
      await submitDecision(result.application_id, decision);
      setDecisionMessage(
        decision === "APPROVED" ? "Decision recorded: Approved." : "Decision recorded: Rejected."
      );
    } catch (err) {
      setDecisionMessage(err instanceof Error ? err.message : "Failed to record decision.");
    }
  }

  const checks = result?.verification_result.checks;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="mb-8 text-3xl font-bold">Inspector Verification</h1>

      <form onSubmit={handleSubmit} className="mb-10 grid gap-4 rounded-xl border border-gray-200 p-6 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-lg font-medium">
          Application ID
          <input
            className="rounded-lg border border-gray-300 px-3 py-2 text-lg"
            value={manifest.application_id}
            onChange={(e) => handleFieldChange("application_id", e.target.value)}
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-lg font-medium">
          Brand Name
          <input
            className="rounded-lg border border-gray-300 px-3 py-2 text-lg"
            value={manifest.brand_name}
            onChange={(e) => handleFieldChange("brand_name", e.target.value)}
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-lg font-medium">
          Class/Type
          <input
            className="rounded-lg border border-gray-300 px-3 py-2 text-lg"
            value={manifest.class_type}
            onChange={(e) => handleFieldChange("class_type", e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-lg font-medium">
          Alcohol By Volume
          <input
            className="rounded-lg border border-gray-300 px-3 py-2 text-lg"
            value={manifest.alcohol_by_volume}
            onChange={(e) => handleFieldChange("alcohol_by_volume", e.target.value)}
            placeholder="45%"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-lg font-medium sm:col-span-2">
          Label Image
          <input
            type="file"
            accept="image/*"
            className="text-lg"
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            required
          />
        </label>

        {error && <p className="text-lg font-semibold text-red-700 sm:col-span-2">{error}</p>}

        <button
          type="submit"
          disabled={isLoading}
          className="rounded-xl bg-blue-700 px-6 py-3 text-xl font-bold text-white hover:bg-blue-800 disabled:opacity-50 sm:col-span-2"
        >
          {isLoading ? "Verifying..." : "Verify Label"}
        </button>
      </form>

      {result && checks && (
        <section className="grid gap-8 sm:grid-cols-2">
          <div>
            <h2 className="mb-4 text-2xl font-bold">Uploaded Label</h2>
            {imagePreviewUrl && (
              <img src={imagePreviewUrl} alt="Uploaded label artwork" className="w-full rounded-xl border border-gray-200" />
            )}
          </div>

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold">Compliance Checklist</h2>
              <LatencyClock latencySeconds={result.latency_seconds} />
            </div>

            <div className="mb-6">
              <StatusBadge status={result.verification_result.overall_status} size="lg" />
            </div>

            <ChecklistRow label="Government Warning" status={checks.government_warning.status} />
            <ChecklistRow label="Brand Name" status={checks.brand_name.status} />
            <ChecklistRow label="Alcohol By Volume" status={checks.alcohol_by_volume.status} />

            <div className="mt-8 flex gap-4">
              <button
                type="button"
                onClick={() => handleDecision("APPROVED")}
                className="rounded-xl bg-green-700 px-6 py-3 text-lg font-bold text-white hover:bg-green-800"
              >
                Approve Mismatch
              </button>
              <button
                type="button"
                onClick={() => handleDecision("REJECTED")}
                className="rounded-xl bg-red-700 px-6 py-3 text-lg font-bold text-white hover:bg-red-800"
              >
                Reject Submission
              </button>
            </div>
            {decisionMessage && <p className="mt-4 text-lg font-medium">{decisionMessage}</p>}
          </div>
        </section>
      )}
    </main>
  );
}
