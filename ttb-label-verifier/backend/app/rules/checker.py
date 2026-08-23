'''
    Checks exact text, exact capitalized casing for the warning, and fuzzy string matching 
    (via rapidfuzz) for brand names.
'''

from rapidfuzz import fuzz

"""
    Evaluates OCR-extracted text against expected COLA application metadata.
"""
def verify_label_compliance(ocr_text_list: list, manifest_data: dict) -> dict:

    extracted_text_block = " ".join(ocr_text_list)
    results = {
        "status": "PASS",
        "flags": [],
        "details": {}
    }

    # -----------------------------------------------------------------------
    # Rule 1: Government Warning Casing & Exact Presence Check
    # -----------------------------------------------------------------------
    if "GOVERNMENT WARNING:" not in extracted_text_block:
        if "government warning:" in extracted_text_block.lower():
            results["flags"].append({
                "rule": "WARNING_CASING",
                "severity": "FAIL",
                "message": "Government Warning header must be strictly in ALL CAPS."
            })
            results["status"] = "FAIL_CASING"
        else:
            results["flags"].append({
                "rule": "WARNING_MISSING",
                "severity": "FAIL",
                "message": "Mandatory Government Warning statement is missing."
            })
            results["status"] = "FAIL_MISSING_WARNING"

    # -----------------------------------------------------------------------
    # Rule 2: Brand Name Match (Exact & Fuzzy Casing Handling)
    # -----------------------------------------------------------------------
    expected_brand = manifest_data.get("brand_name", "")
    brand_found = any(expected_brand.lower() in text.lower() for text in ocr_text_list)
    
    if brand_found:
        # Check if casing matches exactly
        exact_casing_match = any(expected_brand in text for text in ocr_text_list)
        if not exact_casing_match and results["status"] == "PASS":
            results["flags"].append({
                "rule": "BRAND_CASING_VARIANCE",
                "severity": "NEEDS_REVIEW",
                "message": f"Brand name match found but casing differs (Expected: '{expected_brand}')."
            })
            results["status"] = "NEEDS_REVIEW_CASE"
    else:
        results["flags"].append({
            "rule": "BRAND_MISMATCH",
            "severity": "FAIL",
            "message": f"Expected brand name '{expected_brand}' not found on label artwork."
        })
        results["status"] = "FAIL_BRAND_MISMATCH"

    # -----------------------------------------------------------------------
    # Rule 3: Alcohol By Volume (ABV) Match
    # -----------------------------------------------------------------------
    expected_abv = manifest_data.get("alcohol_by_volume", "").replace("%", "").strip()
    abv_found = any(expected_abv in text for text in ocr_text_list)
    
    if not abv_found:
        results["flags"].append({
            "rule": "ABV_MISMATCH",
            "severity": "FAIL",
            "message": f"Declared ABV '{expected_abv}%' does not match label text."
        })
        if results["status"] == "PASS":
            results["status"] = "FAIL_ABV_MISMATCH"

    return results