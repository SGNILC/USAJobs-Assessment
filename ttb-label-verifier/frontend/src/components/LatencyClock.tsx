interface LatencyClockProps {
  latencySeconds: number;
}

export default function LatencyClock({ latencySeconds }: LatencyClockProps) {
  return (
    <p className="text-lg font-medium text-gray-700">
      Verified in <span className="font-bold">{latencySeconds.toFixed(2)}s</span>
    </p>
  );
}
