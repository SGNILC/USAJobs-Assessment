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
| **Sarah Chen (Business)** | Sub-5 second verification latency; intuitive interface for 73-year-old usability benchmark. | Streamlined single-page workflow, high-contrast visual cues, side-by-side verification, and local verification service. |
| **Marcus Williams (IT Admin)** | Outbound firewall blocks cloud ML endpoints; standalone prototype (no COLA integration). | Entirely local OCR and validation stack using OpenCV + EasyOCR running in a Python backend. |
| **Dave Morrison (Senior Agent)** | Human judgment handling; flexible matching for minor casing/punctuation variances. | Fuzzy string matching with explicit **NEEDS REVIEW** handling and manual approval/rejection controls. |
| **Jenny Park (Junior Agent)** | Exact match for mandatory `GOVERNMENT WARNING:` text and glare/angle tolerance. | Strict regex/case check plus OpenCV preprocessing for deskewing, contrast enhancement, and lighting correction. |
| **Janet (Seattle Office)** | Importers dumping 200–300 applications at once in peak season. | Asynchronous ZIP batch pipeline with job polling and CSV export. |

---

## 2. Technology Stack & Skill Set Alignment

* **Backend Framework:** Python 3.11+ with **FastAPI**.
* **Computer Vision & OCR:** **OpenCV** + **EasyOCR**; offline-only execution.
* **Data Processing & Matching:** **NumPy**, **RapidFuzz**.
* **Frontend Application:** **React + TypeScript + Vite**.
* **Database & Persistence:** **SQLite** for audit logging and batch status.
* **Synthetic Data Generation:** Python script used to generate mock label artifacts.

---

## 3. Implementation Phase Breakdown (P1 – P5)

### Phase 1: Environment Setup, Architecture & Schema Definition (P1)

* **Repository structure**

```text
ttb-label-verifier/
├── backend/
│   ├── app/
│   │   ├── core/         # OCR / preprocessing / batch processing
│   │   ├── models/       # database helpers and persistence
│   │   ├── rules/        # TTB check logic
│   │   └── main.py       # FastAPI app
│   ├── tests/            # validation and smoke testing
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
├── sample_data/
├── README.md
├── README2.md
├── Plann_0822.md
└── db/
```

* **As-built input contract**

```json
{
  "application_id": "COLA-2026-00891",
  "brand_name": "OLD TOM DISTILLERY",
  "class_type": "Kentucky Straight Bourbon Whiskey",
  "alcohol_by_volume": "45%",
  "net_contents": "750 mL"
}
```

* **Current verification output contract (actual backend schema)**

```json
{
  "application_id": "COLA-2026-00891",
  "overall_status": "PASS",
  "flags": [
    {
      "rule": "WARNING_MISSING",
      "severity": "FAIL",
      "message": "Mandatory Government Warning statement is missing."
    }
  ],
  "checks": {
    "government_warning": { "status": "FAIL_MISSING_WARNING" },
    "brand_name": { "status": "PASS" },
    "alcohol_by_volume": { "status": "PASS" }
  }
}
```

> Important: the current backend intentionally keeps the check objects minimal (`status` only). The richer `expected`, `extracted`, and `details` fields are optional UI-display metadata, not a required workflow contract.

---

### Phase 2: Offline Vision, Preprocessing & Compliance Rules Engine (P2)

* **Image preprocessing**
  * Deskewing and rotation correction
  * CLAHE-based contrast enhancement
  * Adaptive thresholding for glare and low-contrast images

* **OCR pipeline**
  * Local EasyOCR extraction with OCR text lines returned to the rules engine

* **Rule execution**
  * Government warning presence and exact header enforcement
  * Brand-name normalization and fuzzy mismatch handling
  * ABV extraction and comparison logic

---

### Phase 3: REST API Service & Asynchronous Batch Manager (P3) ✅ COMPLETE

* **Endpoints implemented**
  * `POST /api/v1/verify`
  * `POST /api/v1/verify/batch`
  * `GET /api/v1/batch/{job_id}`
  * `GET /api/v1/batch/{job_id}/export`
  * `GET /health`
  * `POST /api/v1/verify/{application_id}/decision`
  * `GET /api/v1/verify/{application_id}/decision`

* **Implementation notes**
  * Batch processing is handled through `ThreadPoolExecutor` and tracked in SQLite.
  * `backend/app/main.py` returns the current schema consumed by the frontend.
  * `checker.py` was corrected to return `overall_status` plus `checks` entries with simple status values instead of a mismatched schema.

---

### Phase 4: High-Accessibility React Web Interface (P4) ✅ COMPLETE

* **Inspection view**
  * Manifest form and image upload
  * Uploaded image preview and result checklist
  * Agent approve/reject actions
  * Latency display

* **Batch dashboard**
  * `.zip` upload flow
  * Live status polling
  * Summary results and CSV export

* **Frontend contract note**
  * The UI is built to render richer check details when they exist, but the core verification contract remains minimal.
  * This means the frontend should either:
    1. tolerate missing optional fields safely, or
    2. receive those fields explicitly from the backend if richer explanations are required.

---

### Phase 5: Synthetic Test Generator, Benchmarking & Deployment (P5)

* **Completed**
  * Synthetic dataset generation
  * Benchmark runs and quality checks
  * Performance documentation and known limitation notes

* **Current status**
  * Prototype is functioning as a local verification tool.
  * It is not a production-ready regulatory system and should not be treated as such.

---

## 4. Overall Phase 5 Assessment

The project has achieved a working local prototype with an OCR-based verification engine, API layer, batch queue, and accessible frontend. The current system is operational for demonstration and local validation, but it remains a proof-of-concept and not a production or regulatory workflow.

## 5. Open Architectural Questions

1. **Do we want to enrich the backend result schema** with optional `expected`, `extracted`, and `details` fields for each check to support richer justification panels?
2. **Should batch export remain CSV-only**, or would a more formal inspection-oriented export format be needed for downstream workflow handoff?

---

## 6. Notable Implementation Reality Check

The original planning spec described a richer response shape than the current implementation actually emits. The as-built system is intentionally conservative: it exposes the minimum data required for status + manual review and keeps any explanatory metadata optional. This is the correct design for a stable workflow contract and avoids frontend breakage when richer detail is absent.
