import { useCallback, useRef, useState } from "react";
import { submitBatch, getBatchJob, exportBatchCsv } from "../services/api";
import type { BatchJob, BatchResultItem } from "../services/types";
import StatusBadge from "../components/StatusBadge";
import { classifyStatus } from "../utils/status";

type FilterOption = "ALL" | "PASS" | "REVIEW" | "FAIL";

const POLL_INTERVAL_MS = 1000;

export default function BatchPage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<BatchJob | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterOption>("ALL");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const status = await getBatchJob(id);
          setJob(status);
          if (status.status === "COMPLETED") {
            stopPolling();
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to poll job status.");
          stopPolling();
        }
      }, POLL_INTERVAL_MS);
    },
    [stopPolling]
  );

  async function handleZipFile(zipFile: File) {
    if (!zipFile.name.endsWith(".zip")) {
      setError("Please upload a .zip archive file.");
      return;
    }
    setError(null);
    setJob(null);
    try {
      const init = await submitBatch(zipFile);
      setJobId(init.job_id);
      startPolling(init.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch upload failed.");
    }
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) void handleZipFile(dropped);
  }

  async function handleExport() {
    if (!jobId) return;
    const blob = await exportBatchCsv(jobId);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ttb_batch_${jobId}_export.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const results: BatchResultItem[] = job?.summary.results ?? [];
  const filteredResults = results.filter((item) => {
    if (filter === "ALL") return true;
    const variant = classifyStatus(item.status);
    if (filter === "PASS") return variant === "pass";
    if (filter === "REVIEW") return variant === "review";
    return variant === "fail";
  });

  const progressPct =
    job && job.total_items > 0 ? Math.round((job.processed_items / job.total_items) * 100) : 0;

  return (
    <main className="mx-auto max-w-7xl px-6 py-8 text-black">
      <h1 className="mb-6 text-4xl font-black underline decoration-blue-700 decoration-4">
        Batch Queue Processing
      </h1>

      {/* Step-by-Step Accessible Instructions */}
      <section className="mb-8 rounded-3xl border-4 border-gray-900 bg-amber-50 p-8 shadow-xl text-black">
        <h2 className="mb-6 text-3xl font-black text-black flex items-center gap-3 underline decoration-amber-500 decoration-4">
          <span className="text-4xl">📋</span> How to Process a Batch File (3 Easy Steps)
        </h2>

        <ol className="flex flex-col gap-6 text-2xl font-extrabold text-gray-950">
          <li className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gray-900 text-white font-black text-2xl shadow-md">
              1
            </span>
            <div className="pt-1">
              <strong className="text-black font-black">Prepare Your ZIP Folder:</strong> Make sure your folder contains your labels and your <code className="rounded-lg border-2 border-black bg-amber-200 px-2 py-1 text-2xl font-black">manifest.json</code> file, saved together in one <code className="rounded-lg border-2 border-black bg-amber-200 px-2 py-1 text-2xl font-black">.zip</code> file.
            </div>
          </li>

          <li className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gray-900 text-white font-black text-2xl shadow-md">
              2
            </span>
            <div className="pt-1">
              <strong className="text-black font-black">Upload the File:</strong> Click the large blue <span className="text-blue-900 underline">"CHOOSE BATCH FILE (.ZIP)"</span> button below to select your file, or drag and drop your file into the dashed box.
            </div>
          </li>

          <li className="flex items-start gap-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gray-900 text-white font-black text-2xl shadow-md">
              3
            </span>
            <div className="pt-1">
              <strong className="text-black font-black">Export Your Results:</strong> Watch the progress bar fill up. When finished, click the black <span className="text-gray-900 underline">"📥 Export Summary to CSV"</span> button to download your results.
            </div>
          </li>
        </ol>
      </section>

      {/* Drag & Drop Upload Portal */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`mb-8 flex flex-col items-center justify-center rounded-3xl border-4 border-dashed p-12 text-center shadow-lg transition-colors ${
          isDragging ? "border-blue-800 bg-blue-100" : "border-gray-900 bg-white"
        }`}
      >
        <p className="mb-6 text-3xl font-black text-black">
          Drag & Drop `.zip` Batch Archive Here
        </p>
        <label className="cursor-pointer rounded-2xl border-2 border-black bg-blue-800 px-8 py-5 text-2xl font-black text-white hover:bg-blue-900 shadow-md active:scale-95">
          CHOOSE BATCH FILE (.ZIP)
          <input
            type="file"
            accept=".zip"
            className="hidden"
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) void handleZipFile(selected);
            }}
          />
        </label>
      </div>

      {error && (
        <p className="mb-6 rounded-2xl border-4 border-red-800 bg-red-100 p-5 text-2xl font-black text-red-900">
          ⚠️ {error}
        </p>
      )}

      {job?.summary.error && (
        <p className="mb-6 rounded-2xl border-4 border-red-800 bg-red-100 p-5 text-2xl font-black text-red-900">
          ⚠️ {job.summary.error}
        </p>
      )}

      {/* Active Processing Details */}
      {job && !job.summary.error && (
        <section className="rounded-3xl border-4 border-gray-900 bg-white p-8 shadow-2xl">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b-4 border-gray-900 pb-4">
            <p className="text-3xl font-black text-black">
              {job.status === "COMPLETED"
                ? `✓ Completed: ${job.processed_items} of ${job.total_items} Labels Verified`
                : `⏳ Processing Label ${job.processed_items} of ${job.total_items}...`}
            </p>
            {job.status === "COMPLETED" && (
              <button
                type="button"
                onClick={handleExport}
                className="rounded-2xl border-2 border-black bg-black px-8 py-4 text-2xl font-black text-white shadow-lg hover:bg-gray-900 active:scale-95"
              >
                📥 Export Summary to CSV
              </button>
            )}
          </div>

          {/* High-Contrast Progress Bar */}
          <div className="mb-8 h-8 w-full overflow-hidden rounded-full border-2 border-black bg-gray-200">
            <div
              className="h-full bg-blue-800 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Accessible Filter Buttons */}
          <div className="mb-6 flex flex-wrap gap-4">
            {(["ALL", "PASS", "REVIEW", "FAIL"] as FilterOption[]).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setFilter(option)}
                className={`rounded-xl border-2 border-black px-6 py-3 text-xl font-black transition-all ${
                  filter === option
                    ? "bg-blue-800 text-white shadow-md"
                    : "bg-gray-100 text-black hover:bg-gray-200"
                }`}
              >
                SHOW {option}
              </button>
            ))}
          </div>

          {/* High-Contrast Results Table */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border-4 border-gray-900 text-xl">
              <thead>
                <tr className="bg-gray-900 text-white text-left">
                  <th className="p-4 border-r-2 border-gray-700">Application ID</th>
                  <th className="p-4 border-r-2 border-gray-700">Status Outcome</th>
                  <th className="p-4">Latency</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((item) => (
                  <tr key={item.application_id} className="border-b-2 border-gray-900 odd:bg-white even:bg-gray-100">
                    <td className="p-4 border-r-2 border-gray-300 font-extrabold text-black">
                      {item.application_id}
                    </td>
                    <td className="p-4 border-r-2 border-gray-300">
                      <StatusBadge status={item.status} size="md" />
                    </td>
                    <td className="p-4 font-bold text-black">
                      {item.latency_seconds.toFixed(2)}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}