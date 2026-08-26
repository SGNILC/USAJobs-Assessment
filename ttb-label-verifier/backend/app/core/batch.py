import io
import os
import json
import zipfile
import csv
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from app.core.preprocess import extract_text_with_metadata
from app.rules.checker import verify_label_compliance
from app.models.db import create_batch_job, update_batch_progress, log_verification

executor = ThreadPoolExecutor(max_workers=4)

def process_batch_zip(zip_bytes: bytes, job_id: str):
    """
    Extracts ZIP archive containing image files and a manifest.json.
    Processes verifications asynchronously across thread workers.
    """
    results = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        filenames = z.namelist()
        manifest_file = [f for f in filenames if f.endswith("manifest.json") or f.endswith("manifests.json")]
        
        if not manifest_file:
            # Job row must exist before updating it, or the status stays 404 forever
            create_batch_job(job_id, 0)
            update_batch_progress(job_id, 0, 0, summary={"error": "Missing manifest.json in zip archive."})
            return

        try:
            manifest_data = json.loads(z.read(manifest_file[0]))
            manifest_map = {item["application_id"]: item for item in manifest_data}
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            create_batch_job(job_id, 0)
            update_batch_progress(job_id, 0, 0, summary={
                "error": f"manifest.json is malformed or missing 'application_id' fields: {exc}"
            })
            return

        image_files = [f for f in filenames if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        create_batch_job(job_id, len(image_files))

        processed_count = 0
        summary_counts = {"PASS": 0, "NEEDS_REVIEW_CASE": 0, "FAIL_CASING": 0, "FAIL_ABV_MISMATCH": 0, "UNKNOWN": 0}

        for img_name in image_files:
            app_id = os.path.splitext(os.path.basename(img_name))[0]
            app_manifest = manifest_map.get(app_id, {})
            
            img_bytes = z.read(img_name)
            start_time = time.time()
            
            image_quality = {}
            try:
                ocr_text, image_quality = extract_text_with_metadata(img_bytes)
                eval_result = verify_label_compliance(
                    ocr_text, app_manifest, image_quality=image_quality
                )
            except ValueError as exc:
                eval_result = {
                    "overall_status": "INVALID_FILE",
                    "flags": [{"rule": "INVALID_FILE", "severity": "FAIL", "message": str(exc)}],
                    "checks": {},
                }
            latency = round(time.time() - start_time, 2)

            status = eval_result.get("overall_status", "UNKNOWN")
            summary_counts[status] = summary_counts.get(status, 0) + 1
            
            log_verification(app_id, status, latency, eval_result)
            
            results.append({
                "application_id": app_id,
                "status": status,
                "latency_seconds": latency,
                "details": eval_result,
                "image_quality": image_quality,
            })
            
            processed_count += 1
            update_batch_progress(job_id, processed_count, len(image_files), summary={"counts": summary_counts, "results": results})

def generate_batch_csv(summary_data: dict) -> str:
    """Generates CSV formatted report for inspector workflow export."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Application ID", "Overall Status", "Latency (s)", "Brand Check Status", "Government Warning Status", "ABV Check Status"])
    
    for item in summary_data.get("results", []):
        app_id = item.get("application_id", "")
        status = item.get("status", "")
        lat = item.get("latency_seconds", 0.0)
        checks = item.get("details", {}).get("checks", {})
        
        brand_st = checks.get("brand_name", {}).get("status", "N/A")
        warn_st = checks.get("government_warning", {}).get("status", "N/A")
        abv_st = checks.get("alcohol_by_volume", {}).get("status", "N/A")
        
        writer.writerow([app_id, status, lat, brand_st, warn_st, abv_st])
        
    return output.getvalue()
