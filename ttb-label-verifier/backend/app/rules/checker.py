import re
from rapidfuzz import fuzz

def verify_label_compliance(ocr_text_list: list, manifest_data: dict) -> dict:
    """
    Evaluates OCR-extracted text against expected COLA application metadata.
    """
    raw_text_block = " ".join(ocr_text_list)
    clean_text_block = re.sub(r'\s+', ' ', raw_text_block)
    
    results = {
        "status": "PASS",
        "flags": [],
        "details": {}
    }

    # -----------------------------------------------------------------------
    # Rule 1: Government Warning Casing & Presence Check
    # -----------------------------------------------------------------------
    # Flexible regex matches "GOVERNMENT WARNING" even if OCR misses the colon
    has_exact_cap_header = bool(re.search(r'GOVERNMENT\s*WARNING:?', clean_text_block))
    has_lower_cap_header = bool(re.search(r'government\s*warning:?', clean_text_block, re.IGNORECASE))

    if not has_exact_cap_header:
        if has_lower_cap_header:
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
    # Rule 2: Brand Name Match (Exact & Fuzzy Handling)
    # -----------------------------------------------------------------------
    expected_brand = manifest_data.get("brand_name", "")
    
    best_exact_casing_score = 0
    best_case_insensitive_score = 0
    
    for text in ocr_text_list:
        exact_score = fuzz.ratio(expected_brand, text)
        if exact_score > best_exact_casing_score:
            best_exact_casing_score = exact_score
            
        ci_score = fuzz.ratio(expected_brand.lower(), text.lower())
        if ci_score > best_case_insensitive_score:
            best_case_insensitive_score = ci_score

    if best_case_insensitive_score >= 75 or any(expected_brand.lower() in text.lower() for text in ocr_text_list):
        if best_exact_casing_score < 90 and results["status"] == "PASS":
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
        if results["status"] == "PASS":
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