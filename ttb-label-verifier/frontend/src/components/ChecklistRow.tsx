import StatusBadge from "./StatusBadge";

interface ChecklistRowProps {
  label: string;
  status: string;
  detail?: string;
}

export default function ChecklistRow({ label, status, detail }: ChecklistRowProps) {
  return (
    <div className="flex flex-col gap-2 border-b border-gray-200 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-xl font-semibold">{label}</p>
        {detail && <p className="text-base text-gray-600">{detail}</p>}
      </div>
      <StatusBadge status={status} />
    </div>
  );
}
