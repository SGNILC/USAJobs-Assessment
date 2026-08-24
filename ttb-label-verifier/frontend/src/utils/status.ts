export type StatusVariant = "pass" | "review" | "fail";

/** Collapses the checker's granular status codes into one of three visual tiers. */
export function classifyStatus(status: string): StatusVariant {
  if (status === "PASS") return "pass";
  if (status.startsWith("NEEDS_REVIEW")) return "review";
  return "fail";
}

export function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}
