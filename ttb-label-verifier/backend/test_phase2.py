"""Fixture-driven checks for the local OCR and compliance pipeline."""

import json
from pathlib import Path

from app.core.preprocess import extract_text_with_metadata
from app.rules.checker import verify_label_compliance


BACKEND_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = BACKEND_DIR.parent / "sample_data"


def run_tests() -> None:
    fixtures = json.loads((SAMPLE_DATA_DIR / "dataset_index.json").read_text(encoding="utf-8"))
    failures: list[str] = []

    print("\n--- RUNNING PHASE 2 COMPLIANCE VERIFICATION TESTS ---\n")
    for fixture in fixtures:
        image_bytes = (SAMPLE_DATA_DIR / "images" / fixture["image_file"]).read_bytes()
        manifest = json.loads(
            (SAMPLE_DATA_DIR / "manifests" / fixture["manifest_file"]).read_text(encoding="utf-8")
        )
        try:
            ocr_text, image_quality = extract_text_with_metadata(image_bytes)
            result = verify_label_compliance(
                ocr_text, manifest, image_quality=image_quality
            )
        except ValueError:
            result = {"overall_status": "INVALID_FILE"}
            ocr_text = []

        expected = fixture["expected_result"]["overall_status"]
        actual = result["overall_status"]
        passed = actual == expected
        print(f"{'PASS' if passed else 'FAIL'} {fixture['id']}: actual={actual}, expected={expected}")
        if not passed:
            print(f"  OCR: {ocr_text}")
            failures.append(fixture["id"])

    if failures:
        raise AssertionError(f"Fixture status mismatches: {', '.join(failures)}")


if __name__ == "__main__":
    run_tests()
