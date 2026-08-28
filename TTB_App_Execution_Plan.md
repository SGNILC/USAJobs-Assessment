# Architecture & Execution Plan: AI-Powered Alcohol Label Verification App (TTB COLA Prototype)

**Author:** Steeve Gandhi Nsangou  
**Target Environment:** Standalone prototype with a Vercel frontend and Hugging Face backend  
**Workspace File:** `TTB_App_Execution_Plan.md`

---

# Milestone Progress Tracker

* ✅ Phase 1: Environment setup, directory layout, and schema definition
* ✅ Phase 2: offline vision, image preprocessing, and rule verification engine
* ✅ Phase 3: REST API service and asynchronous batch processing manager
* ✅ Phase 4: high-accessibility React web interface
* ✅ Phase 5: benchmarking, testing, deployment configuration, and release readiness review

---

## 1. Stakeholder Requirements & Architectural Mapping

| Stakeholder / Persona | Operational Requirement | Architectural Implementation |
| :--- | :--- | :--- |
| **Business stakeholder** | Fast, understandable review workflow and demonstration-ready prototype | Simplified UI, status badges, image preview, and consistent processing flow |
| **IT / deployment support** | Static frontend with backend logic isolated from strict free-tier limits | Vercel-hosted frontend and Hugging Face-hosted FastAPI backend |
| **Reviewing agent** | Human confirmation of uncertain or edge-case outcomes | Manual approval/rejection flow and queued review workflow |
| **Compliance reviewer** | Rule enforcement for warning text, brand matching, ABV validation | Local OCR plus rule-based checks for key label compliance fields |
| **Operations team** | Batch processing for multiple applications | ZIP upload workflow, async processing, status polling, CSV export |

---

## 2. Technology Stack & Skill Set Alignment

* **Backend framework:** Python with **FastAPI**
* **Computer vision + OCR:** **OpenCV** + **EasyOCR**
* **Data processing + matching:** **NumPy**, **RapidFuzz**
* **Frontend application:** **React + TypeScript + Vite**
* **Database + persistence:** **SQLite**
* **Deployment model:** **Vercel** for frontend and **Hugging Face Spaces** for backend
* **Synthetic data generation:** Python script for mock label images and manifests

---

## 3. Implementation Phase Breakdown

### Phase 1: Environment Setup, Architecture & Schema Definition

**Repository structure**

```text
ttb-label-verifier/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── rules/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env
├── sample_data/
├── render.yaml
├── README.md
├── TTB_App_Execution_Plan.md
└── db/
```

**Input contract**

```json
{
  "application_id": "COLA-2026-00891",
  "brand_name": "OLD TOM DISTILLERY",
  "class_type": "Kentucky Straight Bourbon Whiskey",
  "alcohol_by_volume": "45%",
  "net_contents": "750 mL"
}
```

**Current verification output contract**

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

> The current backend intentionally keeps check objects minimal (`status` only). Richer metadata such as `expected`, `extracted`, and `details` is optional UI-display data rather than a required workflow contract.

---

### Phase 2: Offline Vision, Preprocessing & Compliance Rules Engine

**Image preprocessing**
- deskewing and rotation correction
- CLAHE-based contrast enhancement
- adaptive thresholding for glare and low-contrast images

**OCR pipeline**
- local EasyOCR extraction
- OCR text returned to the rules engine for structured validation

**Rule execution**
- Government Warning presence and header validation
- brand-name normalization and fuzzy mismatch handling
- ABV extraction and comparison logic

---

### Phase 3: REST API Service & Asynchronous Batch Manager

**Endpoints implemented**
- `POST /api/v1/verify`
- `POST /api/v1/verify/batch`
- `GET /api/v1/batch/{job_id}`
- `GET /api/v1/batch/{job_id}/export`
- `GET /health`
- `POST /api/v1/verify/{application_id}/decision`
- `GET /api/v1/verify/{application_id}/decision`

**Implementation notes**
- batch processing is handled asynchronously and tracked in SQLite
- the app returns the schema consumed by the frontend
- the rules engine and API contract intentionally remain minimal to avoid frontend breakage when optional details are absent

---

### Phase 4: High-Accessibility React Web Interface

**Inspection view**
- manifest form and image upload
- uploaded image preview and result checklist
- manual approve/reject decisions
- latency display

**Batch dashboard**
- ZIP upload support
- job-status polling
- summary results and CSV export

**Frontend contract note**
- The UI is designed to render richer metadata when it is available, but it does not depend on it to function.
- This keeps the system stable while still enabling future enhancements.

---

### Phase 5: Synthetic Benchmarking, Release Review & Deployment Model

**Completed**
- synthetic dataset generation
- benchmark execution and recap
- deployment architecture validation using Vercel and Hugging Face
- documentation of known limitations and edge cases

**Current deployment model**
- **Frontend:** Vercel, static React app
- **Backend:** Hugging Face Spaces, FastAPI service running the OCR and compliance logic
- **API host:** direct app URL such as `https://sgnilc-ttb-label-verifier-backend.hf.space`
- **Not to be used as the API target:** the public Hugging Face Spaces landing page URL, which is an HTML wrapper and not the live Uvicorn application

**Current status**
- The prototype is functioning as a demonstration and local validation tool.
- It remains a proof-of-concept rather than a production or regulatory workflow.

---

## 4. Overall Assessment

The project has reached a working prototype state with an OCR-based verification engine, API layer, asynchronous batch workflow, and accessible frontend. The system is operational for demonstration and validation, but it should still be treated as a prototype rather than a production compliance platform.

---

## 5. Future Work: Confidence Rating & Human Review Gating

A strong next enhancement is a confidence rating for each verification result. This rating could combine:

- OCR confidence
- image quality signal
- fuzzy match quality
- rule certainty
- exception severity

This would allow the app to classify results into categories such as:

- high confidence: auto-approve or auto-reject with minimal human intervention
- medium confidence: route to human review
- low confidence: require explicit human approval before final decisioning

This would provide a clearer decision-support layer and help determine when further human approval is necessary.

## 6. Notable Implementation Reality Check

The original planning spec described a richer response shape than the current implementation emits. The as-built system is intentionally conservative: it exposes the minimum data needed for status + human review and leaves explanatory metadata as optional. This is a stable and safe design for the current prototype and avoids frontend breakage when additional detail is absent.
