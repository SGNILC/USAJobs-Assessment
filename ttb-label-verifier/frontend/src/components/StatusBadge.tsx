import { classifyStatus } from "../utils/status";

interface StatusBadgeProps {
  status: string;
  size?: "md" | "lg";
}

export default function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const variant = classifyStatus(status);

  if (variant === "pass") {
    return (
      <div
        className={`inline-flex items-center gap-3 rounded-2xl border-4 border-green-800 bg-green-100 font-extrabold text-green-950 shadow-md ${
          size === "lg" ? "px-6 py-4 text-2xl" : "px-4 py-2 text-xl"
        }`}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-green-700 text-white font-black text-xl">
          ✓
        </span>
        <span>PASS: FULLY COMPLIANT</span>
      </div>
    );
  }

  if (variant === "review") {
    return (
      <div
        className={`inline-flex items-center gap-3 rounded-2xl border-4 border-amber-700 bg-amber-100 font-extrabold text-amber-950 shadow-md ${
          size === "lg" ? "px-6 py-4 text-2xl" : "px-4 py-2 text-xl"
        }`}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-600 text-white font-black text-xl">
          ⚠️
        </span>
        <span>NEEDS REVIEW: MINOR DISCREPANCY</span>
      </div>
    );
  }

  return (
    <div
      className={`inline-flex items-center gap-3 rounded-2xl border-4 border-red-800 bg-red-100 font-extrabold text-red-950 shadow-md ${
        size === "lg" ? "px-6 py-4 text-2xl" : "px-4 py-2 text-xl"
      }`}
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-700 text-white font-black text-xl">
        ✕
      </span>
      <span>FAIL: NON-COMPLIANT</span>
    </div>
  );
}