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
        decision === "APPROVED" ? "✓ Decision recorded: APPROVED" : "✕ Decision recorded: REJECTED"
      );
    } catch (err) {
      setDecisionMessage(err instanceof Error ? err.message : "Failed to record decision.");
    }
  }

  const checks = result?.verification_result.checks;

  return (
    <main className="mx-auto max-w-7xl px-6 py-8 text-black">
      <h1 className="mb-6 text-4xl font-black underline decoration-blue-700 decoration-4">
        Inspector Verification
      </h1>

      {/* Input Form Card */}
      <form
        onSubmit={handleSubmit}
        className="mb-10 grid gap-6 rounded-3xl border-4 border-gray-900 bg-white p-8 shadow-xl sm:grid-cols-2"
      >
        <label className="flex flex-col gap-2 text-2xl font-extrabold text-black">
          Application ID
          <input
            className="rounded-xl border-2 border-gray-900 bg-gray-50 p-4 text-2xl font-bold text-black focus:bg-yellow-50 focus:ring-4 focus:ring-blue-600 outline-none"
            value={manifest.application_id}
            onChange={(e) => handleFieldChange("application_id", e.target.value)}
            placeholder="e.g. COLA-2026-00891"
            required
          />
        </label>

        <label className="flex flex-col gap-2 text-2xl font-extrabold text-black">
          Brand Name
          <input
            className="rounded-xl border-2 border-gray-900 bg-gray-50 p-4 text-2xl font-bold text-black focus:bg-yellow-50 focus:ring-4 focus:ring-blue-600 outline-none"
            value={manifest.brand_name}
            onChange={(e) => handleFieldChange("brand_name", e.target.value)}
            placeholder="e.g. OLD TOM DISTILLERY"
            required
          />
        </label>

        <label className="flex flex-col gap-2 text-2xl font-extrabold text-black">
          Class / Type
          <input
            className="rounded-xl border-2 border-gray-900 bg-gray-50 p-4 text-2xl font-bold text-black focus:bg-yellow-50 focus:ring-4 focus:ring-blue-600 outline-none"
            value={manifest.class_type}
            onChange={(e) => handleFieldChange("class_type", e.target.value)}
            placeholder="e.g. Bourbon Whiskey"
          />
        </label>

        <label className="flex flex-col gap-2 text-2xl font-extrabold text-black">
          Alcohol By Volume (ABV)
          <input
            className="rounded-xl border-2 border-gray-900 bg-gray-50 p-4 text-2xl font-bold text-black focus:bg-yellow-50 focus:ring-4 focus:ring-blue-600 outline-none"
            value={manifest.alcohol_by_volume}
            onChange={(e) => handleFieldChange("alcohol_by_volume", e.target.value)}
            placeholder="e.g. 45%"
            required
          />
        </label>

        <label className="flex flex-col gap-2 text-2xl font-extrabold text-black sm:col-span-2">
          Label Image File
          <input
            type="file"
            accept="image/*"
            className="rounded-xl border-2 border-gray-900 bg-gray-50 p-4 text-xl font-bold text-black cursor-pointer"
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            required
          />
        </label>

        {error && (
          <p className="rounded-xl border-2 border-red-800 bg-red-100 p-4 text-2xl font-black text-red-900 sm:col-span-2">
            ⚠️ {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="rounded-2xl border-2 border-black bg-blue-800 px-8 py-5 text-2xl font-black text-white shadow-lg hover:bg-blue-900 focus:ring-4 focus:ring-yellow-400 active:scale-98 disabled:opacity-50 sm:col-span-2"
        >
          {isLoading ? "🔍 Verifying Label..." : "VERIFY LABEL NOW"}
        </button>
      </form>

      {/* Side-by-Side Verification Result */}
      {result && checks && (
        <section className="grid gap-8 rounded-3xl border-4 border-gray-900 bg-gray-100 p-8 shadow-2xl lg:grid-cols-2">
          {/* Left Column: Label Image */}
          <div className="flex flex-col">
            <h2 className="mb-4 text-3xl font-black text-black">Uploaded Label Image</h2>
            {imagePreviewUrl && (
              <div className="overflow-hidden rounded-2xl border-4 border-gray-900 bg-black p-2 shadow-inner">
                <img
                  src={imagePreviewUrl}
                  alt="Uploaded label artwork"
                  className="max-h-[600px] w-full object-contain"
                />
              </div>
            )}
          </div>

          {/* Right Column: Verification Results */}
          <div className="flex flex-col justify-between">
            <div>
              <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b-4 border-gray-900 pb-4">
                <h2 className="text-3xl font-black text-black">Compliance Results</h2>
                <LatencyClock latencySeconds={result.latency_seconds} />
              </div>

              <div className="mb-6">
                <StatusBadge status={result.verification_result.overall_status} size="lg" />
              </div>

              <div className="flex flex-col gap-2">
                <ChecklistRow
                  label="1. Government Health Warning"
                  status={checks.government_warning.status}
                  // details={checks.government_warning.details}
                />
                <ChecklistRow
                  label="2. Brand Name Match"
                  status={checks.brand_name.status}
                  // expected={checks.brand_name.expected}
                  // extracted={checks.brand_name.extracted}
                  // details={checks.brand_name.flag_reason}
                />
                <ChecklistRow
                  label="3. Alcohol By Volume (ABV)"
                  status={checks.alcohol_by_volume.status}
                  // expected={checks.alcohol_by_volume.expected}
                  // extracted={checks.alcohol_by_volume.extracted}
                />
              </div>
            </div>

            {/* Human Override Actions */}
            <div className="mt-8 border-t-4 border-gray-900 pt-6">
              <p className="mb-4 text-2xl font-extrabold text-black">Inspector Override Decision:</p>
              <div className="flex flex-wrap gap-4">
                <button
                  type="button"
                  onClick={() => handleDecision("APPROVED")}
                  className="flex-1 rounded-2xl border-2 border-black bg-green-700 px-6 py-5 text-2xl font-black text-white shadow-lg hover:bg-green-800 focus:ring-4 focus:ring-yellow-400 active:scale-95"
                >
                  ✓ Approve Mismatch
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision("REJECTED")}
                  className="flex-1 rounded-2xl border-2 border-black bg-red-700 px-6 py-5 text-2xl font-black text-white shadow-lg hover:bg-red-800 focus:ring-4 focus:ring-yellow-400 active:scale-95"
                >
                  ✕ Reject Submission
                </button>
              </div>

              {decisionMessage && (
                <div className="mt-4 rounded-xl border-2 border-blue-900 bg-blue-100 p-4 text-2xl font-black text-blue-950">
                  {decisionMessage}
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}