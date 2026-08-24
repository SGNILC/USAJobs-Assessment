export type CheckStatus = string; // e.g. "PASS" | "FAIL_CASING" | "NEEDS_REVIEW_CASE" | ...

export interface Flag {
  rule: string;
  severity: string;
  message: string;
}

export interface CheckResult {
  status: CheckStatus;
}

export interface VerificationResult {
  overall_status: CheckStatus;
  flags: Flag[];
  checks: {
    government_warning: CheckResult;
    brand_name: CheckResult;
    alcohol_by_volume: CheckResult;
  };
}

export interface VerifyResponse {
  application_id: string;
  latency_seconds: number;
  verification_result: VerificationResult;
  raw_ocr_extracted: string[];
}

export interface ApplicationManifest {
  application_id: string;
  brand_name: string;
  class_type: string;
  alcohol_by_volume: string;
  net_contents?: string;
}

export interface BatchInitResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface BatchResultItem {
  application_id: string;
  status: CheckStatus;
  latency_seconds: number;
  details: VerificationResult;
}

export interface BatchJob {
  job_id: string;
  total_items: number;
  processed_items: number;
  status: "PROCESSING" | "COMPLETED";
  summary: {
    counts?: Record<string, number>;
    results?: BatchResultItem[];
    error?: string;
  };
}

export type AgentDecision = "APPROVED" | "REJECTED";

export interface DecisionResponse {
  application_id: string;
  decision: AgentDecision;
  notes?: string | null;
}
