import io
import json
import zipfile
import time
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

# Initialize in-memory TestClient
client = TestClient(app)

def build_dummy_png() -> bytes:
    """Generates real, decodable 1x1 PNG bytes (hardcoded byte literals are prone to CRC corruption)."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()

def build_mock_zip() -> bytes:
    """Generates an in-memory ZIP file containing sample manifest data and test images."""
    zip_buffer = io.BytesIO()
    
    manifest_data = [
        {
            "application_id": "COLA-2026-TEST01",
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "alcohol_by_volume": "45%",
            "net_contents": "750 mL"
        },
        {
            "application_id": "COLA-2026-TEST02",
            "brand_name": "STONE'S THROW BREWING",
            "class_type": "Craft IPA",
            "alcohol_by_volume": "6.5%",
            "net_contents": "12 oz"
        }
    ]
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write manifest file
        zf.writestr("manifest.json", json.dumps(manifest_data))
        
        # Create lightweight dummy image byte streams for testing
        dummy_image_data = build_dummy_png()
        zf.writestr("COLA-2026-TEST01.png", dummy_image_data)
        zf.writestr("COLA-2026-TEST02.png", dummy_image_data)
        
    return zip_buffer.getvalue()

def run_phase3_tests():
    print("=" * 60)
    print("STARTING PHASE 3 INTEGRATION TEST SUITE (FastAPI TestClient)")
    print("=" * 60)

    # 1. Test Health Check
    print("\n[1/4] Testing GET /health ...")
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    print(f"  ✓ Health Status: {response.json()}")

    # 2. Test Single Application Verification
    print("\n[2/4] Testing POST /api/v1/verify ...")
    single_manifest = {
        "application_id": "COLA-2026-SINGLE",
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Bourbon",
        "alcohol_by_volume": "45%"
    }
    dummy_img = ("test_label.png", build_dummy_png(), "image/png")
    
    response = client.post(
        "/api/v1/verify",
        data={"manifest": json.dumps(single_manifest)},
        files={"file": dummy_img}
    )
    assert response.status_code == 200, f"Single verification failed: {response.text}"
    single_res = response.json()
    print(f"  ✓ Application ID: {single_res['application_id']}")
    print(f"  ✓ Latency: {single_res['latency_seconds']}s")
    print(f"  ✓ Status Outcome: {single_res['verification_result']['overall_status']}")

    # 3. Test Asynchronous Batch Upload
    print("\n[3/4] Testing POST /api/v1/verify/batch ...")
    zip_bytes = build_mock_zip()
    
    response = client.post(
        "/api/v1/verify/batch",
        files={"file": ("sample_batch.zip", zip_bytes, "application/zip")}
    )
    assert response.status_code == 200, f"Batch upload failed: {response.text}"
    batch_init = response.json()
    job_id = batch_init["job_id"]
    print(f"  ✓ Batch Job Triggered! Job ID: {job_id}")

    # 4. Poll Batch Completion & Verify CSV Export
    print("\n[4/4] Polling Batch Job Progress & Verifying CSV Export ...")
    completed = False
    for _ in range(10):  # Poll up to 10 seconds
        status_res = client.get(f"/api/v1/batch/{job_id}").json()
        print(f"  ... Job Status: {status_res['status']} ({status_res['processed_items']}/{status_res['total_items']} processed)")
        
        if status_res["status"] == "COMPLETED":
            completed = True
            break
        time.sleep(0.5)

    assert completed, "Batch job did not complete within timeout."

    # Verify CSV Export Endpoint
    export_res = client.get(f"/api/v1/batch/{job_id}/export")
    assert export_res.status_code == 200, "CSV Export endpoint failed."
    csv_text = export_res.text
    print("\n  ✓ CSV Export Payload Received:")
    print("-" * 40)
    print(csv_text.strip())
    print("-" * 40)

    print("\n✅ ALL PHASE 3 INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_phase3_tests()