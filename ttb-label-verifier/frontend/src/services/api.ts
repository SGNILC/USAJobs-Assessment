import type {
  ApplicationManifest,
  BatchInitResponse,
  BatchJob,
  DecisionResponse,
  AgentDecision,
  VerifyResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

async function parseJsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function verifyLabel(
  file: File,
  manifest: ApplicationManifest
): Promise<VerifyResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("manifest", JSON.stringify(manifest));

  const response = await fetch(`${API_BASE_URL}/api/v1/verify`, {
    method: "POST",
    body: formData,
  });
  return parseJsonOrThrow<VerifyResponse>(response);
}

export async function submitBatch(zipFile: File): Promise<BatchInitResponse> {
  const formData = new FormData();
  formData.append("file", zipFile);

  const response = await fetch(`${API_BASE_URL}/api/v1/verify/batch`, {
    method: "POST",
    body: formData,
  });
  return parseJsonOrThrow<BatchInitResponse>(response);
}

export async function getBatchJob(jobId: string): Promise<BatchJob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/batch/${jobId}`);
  return parseJsonOrThrow<BatchJob>(response);
}

export async function exportBatchCsv(jobId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/batch/${jobId}/export`);
  if (!response.ok) {
    throw new Error(`CSV export failed (${response.status})`);
  }
  return response.blob();
}

export async function submitDecision(
  applicationId: string,
  decision: AgentDecision,
  notes?: string
): Promise<DecisionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/verify/${applicationId}/decision`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes }),
    }
  );
  return parseJsonOrThrow<DecisionResponse>(response);
}
