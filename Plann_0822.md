# Architecture & Execution Plan: AI-Powered Alcohol Label Verification App (TTB COLA Prototype)

**Author:** Steeve Gandhi Nsangou  
**Target Environment:** Standalone Prototype (Air-Gapped / Offline Compliant)  
**Workspace File:** `TTB_App_Execution_Plan.md`
---
# 📊 Overall Milestone Progress Tracker

* ✅ Phase 1: Environment Setup, Directory Layout & Data Schema Definition

* ✅ Phase 2: Offline Vision, Image Preprocessing & Rule Verification Engine

* ✅ Phase 3: REST API Service & Asynchronous Batch Processing Manager

* ✅ Phase 4: High-Accessibility React Web Interface (73-Yo Benchmark)

* 🔄 Phase 5: Automated Benchmarking, Final Testing & Deployment (benchmarking complete; release work remaining)

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

### Phase 3: REST API Service & Asynchronous Batch Manager (P3) ✅ COMPLETE

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

* **Implementation Notes (as-built):**
  * Endpoints implemented in `backend/app/main.py`: `POST /api/v1/verify`, `POST /api/v1/verify/batch`, `GET /api/v1/batch/{job_id}`, `GET /api/v1/batch/{job_id}/export`, plus `GET /health`.
  * Batch processing implemented in `backend/app/core/batch.py` using a `ThreadPoolExecutor`, with progress/summary tracked via `backend/app/models/db.py`.
  * Integration test suite (`backend/test_phase3.py`) exercises health check, single verification, batch upload, job polling, and CSV export end-to-end via FastAPI's `TestClient` — all passing.
  * Fixed defects found during integration testing:
    * Removed a stray/conflicting third-party `app` package from the backend venv that shadowed the local `app` package.
    * Hardened `preprocess.py` to raise a clear `ValueError` on undecodable image bytes instead of an opaque OpenCV assertion failure.
    * Corrected `checker.py`'s output schema to use `overall_status` (previously `status`) and added a `checks` sub-dict (`government_warning`, `brand_name`, `alcohol_by_volume`) to match the schema consumed by `main.py`, `batch.py`, and the Phase 3 test suite.

---

### Phase 4: High-Accessibility React Web Interface (P4) ✅ COMPLETE

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

* **Implementation Notes (as-built):**
  * Scaffolded `frontend/` as a Vite + React + TypeScript app with Tailwind CSS v4 (`@tailwindcss/vite`) and `react-router-dom`.
  * Theme tokens in `frontend/src/index.css` set an 18px base font and WCAG-AAA-oriented green/yellow/red status color tokens.
  * `frontend/src/services/api.ts` + `types.ts` provide a typed client for `verifyLabel`, `submitBatch`, `getBatchJob`, `exportBatchCsv`, and `submitDecision`, reading the backend URL from `VITE_API_BASE_URL`.
  * Added backend support for agent decisions: `agent_decisions` table in `backend/app/models/db.py`, plus `POST/GET /api/v1/verify/{application_id}/decision` in `backend/app/main.py`.
  * Shared components: `StatusBadge`, `ChecklistRow`, `LatencyClock` (in `frontend/src/components/`), driven by a status-classification helper (`frontend/src/utils/status.ts`) that collapses granular rule codes into PASS/NEEDS_REVIEW/FAIL tiers.
  * `/review` page: manifest form + image upload, side-by-side uploaded image vs. checklist, latency clock, and Approve/Reject buttons wired to the decision endpoint.
  * `/batch` page: drag-and-drop `.zip` upload, polling progress bar, filterable results table, and CSV export download.
  * Verified end-to-end against the running backend using real sample data (`sample_data/images/COLA-2026-001.png` + matching manifest) — OCR, rules engine, and decision persistence all confirmed working via direct API calls, and the frontend build (`npm run build`) and dev server both run cleanly.

---

### Phase 5: Synthetic Test Generator, Benchmarking & Deployment (P5)

* **Task 5.1: Synthetic Label Dataset Generator (`sample_data/generate_mock_labels.py`) ✅ COMPLETE**
  * Deterministic corpus contains 20 cases covering passing labels, warning casing/text/missing cases, brand variance/mismatch, ABV mismatch/missing cases, rotation, glare, low contrast, combined artifacts, and a corrupt image.
  * `dataset_index.json` records each fixture's expected status and artifact metadata.

* **Task 5.2: Latency & Accuracy Automated Benchmark Suite ✅ COMPLETE**
  * `backend/benchmark_phase5.py` writes `backend/benchmark.json` by default and records per-case status, confidence, latency, preprocessing/OCR timing, and failures.
  * Reproduce the benchmark from the repository root with: `backend\venv\Scripts\python.exe backend\benchmark_phase5.py --limit 20 --output backend\benchmark.json`.
  * Best recorded EasyOCR run: 19/20 correct (95%). CPU-only PyTorch was confirmed (`2.13.0+cpu`, CUDA unavailable, no `nvidia-smi`).
  * EasyOCR latency was approximately 5-8 seconds per image, so the five-second target is not met in this environment.
  * Tesseract benchmark: approximately 25-35% accuracy with sub-second average latency; rejected for final decisions because accuracy is insufficient.
  * The 1024-pixel test reduced speed only marginally and reduced accuracy to 20-30%; the working setting remains 1280 pixels.
  * Known fixture issue: `COLA-2026-016` returns `PASS` instead of `NEEDS_REVIEW` because measured glare was `0.0` and the quality gate requires both glare and low contrast.

* **Task 5.3: Release hardening 🔄 IN PROGRESS**
  * Removed the abandoned Tesseract execution path from the active EasyOCR pipeline and retained one global OCR reader.
  * Added confidence and manual-review metadata to single and batch results; fixed JSON serialization of crop bounds.
  * Remaining: verify the current end-to-end test run after cleanup, review upload/configuration behavior, and improve the `COLA-2026-016` quality heuristic if time permits.

* **Task 5.4: Repository & Deployment ⏳ NOT STARTED**
  * Finalize README setup/run instructions, known limitations, benchmark evidence, and offline-network assumptions.
  * Deploy the working prototype to one selected target and smoke-test health, single verification, batch polling/export, and agent decisions.

---

## 4. Overall Phase 5 Assessment

Phase 5 has produced a measurable prototype, but not a production-ready deployment. Accuracy is strong on the synthetic corpus when EasyOCR and the 1280-pixel CLAHE path are used; throughput is limited by the available CPU-only environment. Confidence metadata and manual-review routing reduce operational risk for larger batches, but they do not replace human review or guarantee correctness. The remaining work is release hardening, final documentation, deployment, and acceptance evidence.

## 5. Architectural Alignment Questions

1. **Pre-packaged Sample Data:** Should we include a pre-configured batch ZIP file (`sample_batch_200.zip`) directly inside the `sample_data/` directory so reviewers can test the 200–300 application queue with a single click?
2. **Export Formatting:** For the batch export functionality, is a standard `.csv` file sufficient, or would an `.xlsx` file formatted to match federal inspection templates be preferred?
