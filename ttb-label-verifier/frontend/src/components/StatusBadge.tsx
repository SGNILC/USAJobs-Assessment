import { classifyStatus, statusLabel } from "../utils/status";

interface StatusBadgeProps {
  status: string;
  size?: "md" | "lg";
}

const VARIANT_STYLES: Record<string, string> = {
  pass: "bg-status-pass-bg text-status-pass-fg border-status-pass-border",
  review: "bg-status-review-bg text-status-review-fg border-status-review-border",
  fail: "bg-status-fail-bg text-status-fail-fg border-status-fail-border",
};

const VARIANT_ICON: Record<string, string> = {
  pass: "\u2713",
  review: "\u26A0",
  fail: "\u2715",
};

export default function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const variant = classifyStatus(status);
  const sizeClasses = size === "lg" ? "text-2xl px-5 py-3" : "text-lg px-4 py-2";

  return (
    <span
      role="status"
      className={`inline-flex items-center gap-2 rounded-lg border-2 font-bold ${sizeClasses} ${VARIANT_STYLES[variant]}`}
    >
      <span aria-hidden="true">{VARIANT_ICON[variant]}</span>
      {statusLabel(status)}
    </span>
  );
}
