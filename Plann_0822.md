# Architecture & Execution Plan: AI-Powered Alcohol Label Verification App (TTB COLA Prototype)

**Author:** Steeve Gandhi Nsangou  
**Target Environment:** Standalone Prototype (Air-Gapped / Offline Compliant)  
**Workspace File:** `TTB_App_Execution_Plan.md`

---

## 1. Stakeholder Requirements & Architectural Mapping

| Stakeholder / Persona | Operational Requirement | Architectural Implementation |
| :--- | :--- | :--- |
| **Sarah Chen (Business)** | Sub-5 second verification latency; intuitive interface for 73-year-old usability benchmark. | Streamlined single-page workflow, high-contrast visual cues (Green/Yellow/Red), side-by-side verification, sub-second Python backend. |
| **Marcus Williams (IT Admin)** | Outbound firewall blocks cloud ML endpoints; standalone prototype (no COLA integration). | Entirely local, offline vision model (`EasyOCR` / `PyTesseract` + `OpenCV`) running in Python container; zero cloud API dependency. |
| **Dave Morrison (Senior Agent)** | Human judgment handling; flexible matching for minor casing/punctuation variances. | Fuzzy string matching with explicit **NEEDS REVIEW** status and manual agent override controls (Approve/Reject). |
| **Jenny Park (Junior Agent)** | Exact match for mandatory `"GOVERNMENT WARNING:"` (ALL CAPS/Bold); glare/angle tolerance. | Dual-rule matching engine: Strict regex/case check for health warning; OpenCV image deskewing and CLAHE contrast enhancement for bad lighting/glare. |
| **Janet (Seattle Office)** | Importers dumping 200–300 applications at once in peak season. | Asynchronous batch upload pipeline accepting `.zip` archives with concurrent worker processing and CSV/Excel export. |

---

## 2. Technology Stack & Skill Set Alignment

The architecture leverages tools directly matching candidate experience while respecting federal infrastructure constraints.

* **Backend Framework:** Python 3.11+ with **FastAPI** (asynchronous REST endpoints, native Pydantic validation).
* **Computer Vision & OCR:** **OpenCV** (image preprocessing, deskewing, binarization) + **EasyOCR / PyTesseract** (100% offline text extraction).
* **Data Processing & Matching:** **pandas**, **NumPy**, **RapidFuzz** (token ratio and Levenshtein distance calculations).
* **Frontend Application:** **React / React Native Web (Expo)** (high-contrast, responsive UI designed in Figma).
* **Database & Persistence:** **SQLite** with parameterized queries (local-first storage for audit logging and batch status).
* **Synthetic Data Generation:** **Pillow (PIL)** Python script to programmatically synthesize sample label artwork.

---

## 3. Implementation Phase Breakdown (P1 – P5)

---

### Phase 1: Environment Setup, Architecture & Schema Definition (P1)

* **Task 1.1: Workspace & Directory Initialization (VS Code)**
  * Repository structure:
    ```text
    ttb-label-verifier/
    ├── backend/
    │   ├── app/
    │   │   ├── api/          # FastAPI routes (single, batch, status, export)
    │   │   ├── core/         # Image preprocessing & local OCR pipeline
    │   │   ├── rules/        # Verification algorithms (Warning, Brand, ABV)
    │   │   ├── models/       # Pydantic schemas & SQLite ORM/queries
    │   │   └── utils/        # Export helpers (CSV / Excel formatters)
    │   ├── tests/            # Unit & benchmark test suites
    │   └── requirements.txt
    ├── frontend/             # React / Expo Web Workspace
    │   ├── src/
    │   │   ├── components/   # High-contrast UI elements, status badges
    │   │   ├── pages/        # Inspector Review, Batch Queue, Audit Logs
    │   │   └── services/     # API integration client
    │   └── package.json
    ├── sample_data/          # Mock label generator & synthetic dataset
    └── README.md
    ```

* **Task 1.2: Pydantic Data Contract Specs**
  * Incoming Application Schema:
    ```json
    {
      "application_id": "COLA-2026-00891",
      "brand_name": "OLD TOM DISTILLERY",
      "class_type": "Kentucky Straight Bourbon Whiskey",
      "alcohol_by_volume": "45%",
      "net_contents": "750 mL"
    }
    ```
  * Verification Result Output Schema:
    ```json
    {
      "application_id": "COLA-2026-00891",
      "overall_status": "PASS | FAIL | NEEDS_REVIEW",
      "latency_seconds": 1.84,
      "checks": {
        "government_warning": {
          "status": "PASS | FAIL",
          "header_capitalized": true,
          "verbatim_match": true,
          "details": "Header 'GOVERNMENT WARNING:' detected in ALL CAPS."
        },
        "brand_name": {
          "status": "PASS | NEEDS_REVIEW | FAIL",
          "expected": "OLD TOM DISTILLERY",
          "extracted": "Old Tom Distillery",
          "match_score": 100.0,
          "flag_reason": "Case mismatch detected ('OLD TOM DISTILLERY' vs 'Old Tom Distillery'). Flagged for agent review."
        },
        "alcohol_by_volume": {
          "status": "PASS | FAIL",
          "expected": "45%",
          "extracted": "45% Alc./Vol."
        }
      },
      "extracted_text_raw": "..."
    }
    ```

---

### Phase 2: Offline Vision, Preprocessing & Compliance Rules Engine (P2)

* **Task 2.1: Image Artifact Resilience Preprocessing (`backend/app/core/preprocess.py`)**
  * Apply OpenCV transformations to correct real-world photo flaws:
    * **Deskewing & Auto-Rotation:** Calculate text orientation vectors to straighten angled photos.
    * **Contrast Enhancement (CLAHE):** Normalize local contrast to eliminate bottle glare and shadow artifacts.
    * **Binarization:** Adaptive thresholding for low-light extraction.
  * *Target Preprocessing Budget:* $< 300\text{ms}$.

* **Task 2.2: Local Offline OCR Pipeline (`backend/app/core/ocr.py`)**
  * Initialize local `EasyOCR` / `PyTesseract` engine (zero outbound cloud connections).
  * Extract text bounding boxes, string lines, and optical confidence scores.

* **Task 2.3: Regulatory Rule Execution Engine (`backend/app/rules/`)**
  * **Rule A: Government Health Warning (Strict Exact Check)**
    * Regex scan for `"GOVERNMENT WARNING:"`.
    * Assert header is $100\%$ upper case.
    * Exact string matching against mandatory text:
      > *"ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."*
    * Any casing, omission, or wording alteration instantly flags `FAIL`.
  * **Rule B: Brand Name & Class/Type Matching (Fuzzy Judgment Logic)**
    * String normalization (removing punctuation/whitespace).
    * `RapidFuzz` token set ratio calculation.
    * Score $\ge 95\% \rightarrow$ `PASS`; Score $75\% - 94\% \rightarrow$ `NEEDS_REVIEW` (Highlights capitalization/punctuation differences like `"STONE'S THROW"` vs `"Stone's Throw"`); Score $< 75\% \rightarrow$ `FAIL`.
  * **Rule C: ABV & Volume Regex Parsing**
    * Numerical match on percentage formats (e.g., `45%`, `45.0% ABV`, `45% Alc./Vol.`) and metric unit statements (`750 mL`, `1.5 L`).

---

### Phase 3: REST API Service & Asynchronous Batch Manager (P3)

* **Task 3.1: Single Application Endpoint (`POST /api/v1/verify/single`)**
  * Receives label image file + form meta. Executes Preprocess $\rightarrow$ OCR $\rightarrow$ Rules Engine.
  * Returns structured JSON compliance report. Target processing time: $< 3.5\text{s}$ (well within the 5-second requirement).

* **Task 3.2: Asynchronous Batch Endpoint (`POST /api/v1/verify/batch`)**
  * Accepts `.zip` archive containing up to 300 label images and a manifest CSV/JSON.
  * Dispatches jobs via Python `concurrent.futures.ThreadPoolExecutor` for asynchronous multi-worker execution.
  * Exposes job progress endpoint (`GET /api/v1/batch/{job_id}`) returning total, completed, passed, flagged, and failed counts.
  * Includes CSV/Excel exporter (`GET /api/v1/batch/{job_id}/export`) for agent workflow integration.

* **Task 3.3: Storage & Audit Trail Layer**
  * Embedded SQLite database storing execution time metrics, confidence scores, and verification outcomes using parameterized queries.

---

### Phase 4: High-Accessibility React Web Interface (P4)

* **Task 4.1: Accessible Interface Engineering ("73-Year-Old Usability Benchmark")**
  * High-contrast design, large text sizes ($18\text{pt}+$ base font), and prominent action controls.
  * Clear, unequivocal visual status indicators:
    * **GREEN BADGE (PASS):** Large checkmark, green background card.
    * **YELLOW BADGE (NEEDS REVIEW):** Distinct alert highlighting specific discrepancy (e.g., casing variance).
    * **RED BADGE (FAIL):** Direct callout of non-compliant element (e.g., Missing Warning Header).

* **Task 4.2: Inspector Verification View (`/review`)**
  * Side-by-side comparison interface: Uploaded Label Image (with OCR bounding box highlights) vs. Application Data Checklist.
  * Real-time latency clock showing verification speed (e.g., "Verified in 1.8 seconds").
  * Manual agent override buttons ("Approve Mismatch", "Reject Submission") honoring human agent judgment.

* **Task 4.3: Batch Queue Dashboard (`/batch`)**
  * Drag-and-drop `.zip` submission portal.
  * Real-time progress bar with live counter (e.g., "Processing Label 142 of 300").
  * Filterable batch data table (Filter by: All, Needs Review, Failed, Passed) with "Export Summary to CSV" button.

---

### Phase 5: Synthetic Test Generator, Benchmarking & Deployment (P5)

* **Task 5.1: Synthetic Label Dataset Generator (`sample_data/generate_mock_labels.py`)**
  * Python script utilizing `Pillow` to generate 20+ test images:
    * Standard compliant spirits, wine, and craft beer labels.
    * Non-compliant labels: Lowercase `"Government Warning:"`, altered text, missing ABV, mismatched brand names.
    * Artifact test cases: Rotated labels, synthetic glare, and low-contrast background images.

* **Task 5.2: Latency & Accuracy Automated Benchmark Suite**
  * Execution script verifying that single label processing times remain strictly under $5\text{s}$ across all test cases.

* **Task 5.3: Repository & Deployment**
  * Deploy working application prototype to public URL (Render / Railway / Vercel).
  * Finalize `README.md` detailing quickstart commands, local docker setup, architectural trade-offs, and offline network compliance.

---

## 4. Architectural Alignment Questions

1. **Pre-packaged Sample Data:** Should we include a pre-configured batch ZIP file (`sample_batch_200.zip`) directly inside the `sample_data/` directory so reviewers can test the 200–300 application queue with a single click?
2. **Export Formatting:** For the batch export functionality, is a standard `.csv` file sufficient, or would an `.xlsx` file formatted to match federal inspection templates be preferred?
