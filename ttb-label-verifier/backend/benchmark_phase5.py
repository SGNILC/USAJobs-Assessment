"""Benchmark the local OCR and compliance pipeline against the fixture corpus.

Run from the backend directory with ``python benchmark_phase5.py``. Use
``--output`` to save the report as JSON without changing the fixture data.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from app.core.preprocess import extract_text_with_metadata
from app.rules.checker import verify_label_compliance


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATASET_DIR = PROJECT_DIR / "sample_data"
DEFAULT_INDEX = DATASET_DIR / "dataset_index.json"


def percentile(values: list[float], fraction: float) -> float:
    """Return a simple nearest-rank percentile for a non-empty list."""
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


def run_benchmark(index_path: Path, max_seconds: float, limit: int | None = None) -> dict[str, Any]:
    with index_path.open(encoding="utf-8") as index_file:
        fixtures = json.load(index_file)
    if limit is not None:
        fixtures = fixtures[:limit]

    cases: list[dict[str, Any]] = []
    latencies: list[float] = []

    for fixture in fixtures:
        print(f"Benchmarking {fixture['id']} — {fixture['scenario']}...", flush=True)

        expected = fixture["expected_result"]["overall_status"]
        image_path = DATASET_DIR / "images" / fixture["image_file"]
        manifest_path = DATASET_DIR / "manifests" / fixture["manifest_file"]

        with manifest_path.open(encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
        image_bytes = image_path.read_bytes()

        started = time.perf_counter()
        error: str | None = None
        image_quality: dict[str, Any] = {}
        try:
            extracted_text, image_quality = extract_text_with_metadata(image_bytes)
            result = verify_label_compliance(
                extracted_text, manifest, image_quality=image_quality
            )
            actual = result["overall_status"]
        except ValueError as exc:
            actual = "INVALID_FILE"
            error = str(exc)
        except Exception as exc:  # Keep the report useful for unexpected cases.
            actual = "ERROR"
            error = f"{type(exc).__name__}: {exc}"

        latency = time.perf_counter() - started
        latencies.append(latency)
        cases.append(
            {
                "id": fixture["id"],
                "scenario": fixture["scenario"],
                "expected_status": expected,
                "actual_status": actual,
                "status_match": actual == expected,
                "latency_seconds": round(latency, 4),
                "under_latency_gate": latency <= max_seconds,
                "processing_breakdown_seconds": {
                    "preprocess": image_quality.get("preprocess_seconds", 0.0),
                    "ocr": image_quality.get("ocr_seconds", 0.0),
                },
                "error": error,
            }
        )

    status_matches = sum(case["status_match"] for case in cases)
    latency_failures = [case for case in cases if not case["under_latency_gate"]]
    functional_failures = [case for case in cases if not case["status_match"]]

    report = {
        "fixture_count": len(cases),
        "status_matches": status_matches,
        "accuracy": round(status_matches / len(cases), 4) if cases else 0.0,
        "latency_gate_seconds": max_seconds,
        "latency_seconds": {
            "mean": round(statistics.mean(latencies), 4) if latencies else 0.0,
            "p50": round(percentile(latencies, 0.50), 4) if latencies else 0.0,
            "p95": round(percentile(latencies, 0.95), 4) if latencies else 0.0,
            "max": round(max(latencies), 4) if latencies else 0.0,
        },
        "functional_failures": functional_failures,
        "latency_failures": latency_failures,
        "cases": cases,
        "acceptance_passed": not functional_failures and not latency_failures,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--max-seconds", type=float, default=5.0)
    parser.add_argument("--limit", type=int, help="Run only the first N fixtures while profiling.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_benchmark(args.index, args.max_seconds, args.limit)
    print(json.dumps(report, indent=2))

    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 0 if report["acceptance_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
