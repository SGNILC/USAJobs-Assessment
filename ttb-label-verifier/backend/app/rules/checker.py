"""TTB label compliance checks for warning text, brand, and ABV."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz


MANDATORY_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD "
    "NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF "
    "BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY "
    "TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)


def _normalise(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def _set_failure(results: dict[str, Any], check: str, status: str, rule: str, message: str) -> None:
    results["checks"][check]["status"] = status
    results["flags"].append({"rule": rule, "severity": "FAIL", "message": message})
    if results["overall_status"] == "PASS":
        results["overall_status"] = status


def verify_label_compliance(
    ocr_text_list: list[str],
    manifest_data: dict[str, Any],
    image_quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate OCR text against application metadata and optional image quality."""
    raw_text = " ".join(ocr_text_list)
    compact_text = _normalise(raw_text)
    results: dict[str, Any] = {
        "overall_status": "PASS",
        "flags": [],
        "checks": {
            "government_warning": {"status": "PASS"},
            "brand_name": {"status": "PASS"},
            "alcohol_by_volume": {"status": "PASS"},
        },
    }

    exact_header = bool(re.search(r"GOVERNMENT\s*WARNING:?", raw_text))
    any_header = bool(re.search(r"government\s*warning:?", raw_text, re.IGNORECASE))
    if not exact_header:
        if any_header:
            _set_failure(results, "government_warning", "FAIL_CASING", "WARNING_CASING", "Government Warning header must be strictly in ALL CAPS.")
        else:
            _set_failure(results, "government_warning", "FAIL_MISSING_WARNING", "WARNING_MISSING", "Mandatory Government Warning statement is missing.")
    elif _normalise(MANDATORY_WARNING) not in compact_text:
        _set_failure(results, "government_warning", "FAIL_WARNING_TEXT", "WARNING_TEXT", "Government Warning statement does not match the required text.")

    expected_brand = manifest_data.get("brand_name", "")
    normalised_brand = _normalise(expected_brand)
    line_matches = [(line, _normalise(line)) for line in ocr_text_list]
    exact_brand_line = next((line for line, candidate in line_matches if candidate == normalised_brand), None)
    contains_exact_brand = any(normalised_brand and normalised_brand in candidate for _, candidate in line_matches)
    best_score = max((fuzz.ratio(normalised_brand, candidate) for _, candidate in line_matches), default=0.0)

    if exact_brand_line is not None or contains_exact_brand:
        if expected_brand not in ocr_text_list and results["overall_status"] == "PASS":
            results["checks"]["brand_name"]["status"] = "NEEDS_REVIEW_CASE"
            results["flags"].append({"rule": "BRAND_CASING_VARIANCE", "severity": "NEEDS_REVIEW", "message": f"Brand name matches after normalisation but differs in presentation (expected '{expected_brand}')."})
            results["overall_status"] = "NEEDS_REVIEW_CASE"
    elif best_score >= 95:
        if results["overall_status"] == "PASS":
            results["checks"]["brand_name"]["status"] = "NEEDS_REVIEW_CASE"
            results["flags"].append({"rule": "BRAND_NEAR_MATCH", "severity": "NEEDS_REVIEW", "message": f"Brand name is a near match (score {best_score:.1f}); manual review required."})
            results["overall_status"] = "NEEDS_REVIEW_CASE"
    else:
        _set_failure(results, "brand_name", "FAIL_BRAND_MISMATCH", "BRAND_MISMATCH", f"Expected brand name '{expected_brand}' not found on label artwork.")

    expected_abv = manifest_data.get("alcohol_by_volume", "").replace("%", "").strip()
    expected_value = float(expected_abv) if expected_abv else None
    detected_abv = [float(value) for value in re.findall(r"(?<!\d)(\d+(?:\.\d+)?)\s*%", raw_text)]
    if expected_value is not None and not any(abs(value - expected_value) < 0.001 for value in detected_abv):
        _set_failure(results, "alcohol_by_volume", "FAIL_ABV_MISMATCH", "ABV_MISMATCH", f"Declared ABV '{expected_abv}%' does not match label text.")

    if image_quality and image_quality.get("needs_review") and results["overall_status"] == "PASS":
        results["overall_status"] = "NEEDS_REVIEW"
        results["flags"].append({"rule": "IMAGE_QUALITY", "severity": "NEEDS_REVIEW", "message": "Combined glare and low contrast may require manual review."})

    return results
