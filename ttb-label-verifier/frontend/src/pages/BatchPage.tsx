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
      setError("Please upload a .zip archive.");
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

  const progressPct = job && job.total_items > 0 ? Math.round((job.processed_items / job.total_items) * 100) : 0;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="mb-8 text-3xl font-bold">Batch Queue</h1>

      {/* <div className="mb-8 rounded-xl border border-gray-200 bg-gray-50 p-6 text-lg">
        <p className="mb-2 font-semibold">
          Upload a <code className="rounded bg-gray-200 px-1">.zip</code> file containing your label images
          (<code className="rounded bg-gray-200 px-1">.png</code>/<code className="rounded bg-gray-200 px-1">.jpg</code>)
          and a file named exactly <code className="rounded bg-gray-200 px-1">manifest.json</code>.
        </p>
        <p className="mb-2">
          <code className="rounded bg-gray-200 px-1">manifest.json</code> must be a JSON array with one object per
          image, each including <code className="rounded bg-gray-200 px-1">application_id</code>,{" "}
          <code className="rounded bg-gray-200 px-1">brand_name</code>,{" "}
          <code className="rounded bg-gray-200 px-1">class_type</code>,{" "}
          <code className="rounded bg-gray-200 px-1">alcohol_by_volume</code>, and{" "}
          <code className="rounded bg-gray-200 px-1">net_contents</code>. The{" "}
          <code className="rounded bg-gray-200 px-1">application_id</code> must match each image's filename
          (without extension).
        </p>
        <a
          href="/sample-manifest.json"
          download
          className="font-semibold text-blue-700 underline hover:text-blue-900"
        >
          Download sample manifest.json
        </a>
      </div> */}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`mb-8 flex flex-col items-center justify-center rounded-xl border-4 border-dashed p-12 text-center text-xl ${
          isDragging ? "border-blue-600 bg-blue-50" : "border-gray-300"
        }`}
      >
        <p className="mb-4 font-semibold">Drag & drop a .zip batch archive here</p>
        <label className="cursor-pointer rounded-xl bg-blue-700 px-6 py-3 font-bold text-white hover:bg-blue-800">
          Choose File
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

      {error && <p className="mb-6 text-lg font-semibold text-red-700">{error}</p>}

      {job?.summary.error && (
        <p className="mb-6 rounded-xl border-2 border-red-700 bg-red-50 p-4 text-lg font-semibold text-red-700">
          {job.summary.error}
        </p>
      )}

      {job && !job.summary.error && (
        <section>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xl font-semibold">
              {job.status === "COMPLETED"
                ? `Completed: ${job.processed_items} of ${job.total_items} processed`
                : `Processing Label ${job.processed_items} of ${job.total_items}`}
            </p>
            {job.status === "COMPLETED" && (
              <button
                type="button"
                onClick={handleExport}
                className="rounded-xl bg-gray-800 px-5 py-2 text-lg font-bold text-white hover:bg-black"
              >
                Export Summary to CSV
              </button>
            )}
          </div>

          <div className="mb-8 h-4 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-blue-700 transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <div className="mb-6 flex gap-3">
            {(["ALL", "PASS", "REVIEW", "FAIL"] as FilterOption[]).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setFilter(option)}
                className={`rounded-lg px-4 py-2 text-lg font-semibold ${
                  filter === option ? "bg-blue-700 text-white" : "bg-gray-100 text-gray-800"
                }`}
              >
                {option}
              </button>
            ))}
          </div>

          <table className="w-full border-collapse text-lg">
            <thead>
              <tr className="border-b-2 border-gray-300 text-left">
                <th className="py-2">Application ID</th>
                <th className="py-2">Status</th>
                <th className="py-2">Latency (s)</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.map((item) => (
                <tr key={item.application_id} className="border-b border-gray-200">
                  <td className="py-2">{item.application_id}</td>
                  <td className="py-2">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="py-2">{item.latency_seconds.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}
