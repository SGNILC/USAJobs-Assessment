'''
    Testing the verification of the label contents
'''

import os
import json
from app.core.preprocess import extract_text_from_image
from app.rules.checker import verify_label_compliance

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")

def run_tests():
    index_path = os.path.join(SAMPLE_DATA_DIR, "dataset_index.json")
    with open(index_path, "r") as f:
        tests = json.load(f)

    print("\n--- RUNNING PHASE 2 COMPLIANCE VERIFICATION TESTS ---\n")
    for test in tests:
        img_path = os.path.join(SAMPLE_DATA_DIR, "images", test["image_file"])
        manifest_path = os.path.join(SAMPLE_DATA_DIR, "manifests", test["manifest_file"])

        with open(img_path, "rb") as f:
            image_bytes = f.read()

        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        # 1. OCR Extraction
        ocr_text = extract_text_from_image(image_bytes)
        
        # 2. Rule Evaluation
        result = verify_label_compliance(ocr_text, manifest_data)
        
        # 3. Output comparison
        passed = result["status"] == test["expected_status"]
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} ID: {test['id']} | Result: {result['status']} | Expected: {test['expected_status']}")

if __name__ == "__main__":
    run_tests()