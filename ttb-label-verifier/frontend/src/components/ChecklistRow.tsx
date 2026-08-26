import StatusBadge from "./StatusBadge";

interface ChecklistRowProps {
  label: string;
  status: string;
  details?: string;
  expected?: string;
  extracted?: string;
}

export default function ChecklistRow({
  label,
  status,
  details,
  expected,
  extracted,
}: ChecklistRowProps) {
  return (
    <div className="mb-4 rounded-2xl border-2 border-gray-900 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <span className="text-2xl font-black text-black">{label}</span>
        <StatusBadge status={status} size="md" />
      </div>

      {(expected || extracted || details) && (
        <div className="mt-3 rounded-xl border border-gray-300 bg-gray-50 p-4 text-xl">
          {expected && (
            <p className="text-gray-900 font-medium">
              <strong className="font-extrabold text-black">Expected:</strong> {expected}
            </p>
          )}
          {extracted && (
            <p className="text-gray-900 font-medium">
              <strong className="font-extrabold text-black">Extracted:</strong> {extracted}
            </p>
          )}
          {details && (
            <p className="mt-1 font-bold text-blue-950 border-t border-gray-200 pt-2">
              🔍 {details}
            </p>
          )}
        </div>
      )}
    </div>
  );
}