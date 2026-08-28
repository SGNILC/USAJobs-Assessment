# TTB Label Verification Prototype

## Purpose

This project is a standalone prototype for reviewing alcohol beverage labels against application metadata. It validates fields such as brand name, class/type, alcohol by volume (ABV), and the required Government Warning statement while leaving final judgment to a human reviewer.

The system demonstrates an end-to-end workflow that includes:

- image upload
- local OCR extraction
- rule-based compliance checks
- asynchronous batch processing
- a manual review interface for final decisioning

This prototype was developed for demonstration, internal evaluation, and workflow exploration. It is not intended for formal regulatory decisions, production compliance use, or integration with the official TTB COLA system.

## Architecture

The current implementation uses a split deployment model:

- Frontend: React + Vite app hosted on Vercel
- Backend: FastAPI service hosted on Hugging Face Spaces
- API communication: frontend fetch calls target the direct Hugging Face app URL rather than the public Hugging Face Spaces landing page

This architecture was chosen to keep the frontend lightweight while offloading the OCR and compliance logic to a backend that can run the required Python stack without the strict memory limitations of a simple free-tier static hosting model.

## Deployment configuration

### Frontend (Vercel)

The deployed frontend is available at:

- https://usa-jobs-assessment-vbw3.vercel.app/

The frontend reads the API base URL from environment variables, and the correct backend base should be:

- https://sgnilc-ttb-label-verifier-backend.hf.space

This is the direct application host. It is not the website URL shown in the Hugging Face Spaces UI wrapper.

### Backend (Hugging Face)

The backend is served by a FastAPI app running on a Hugging Face Space. The application exposes endpoints under `/api/v1/...` and supports CORS for the Vercel frontend origin.

The direct backend host is:

- https://sgnilc-ttb-label-verifier-backend.hf.space

The workspace should not use the Hugging Face Spaces landing page URL (`https://huggingface.co/spaces/...`) as an API target. That page is not the running app server and will trigger HTML 404 responses and browser CORS blocks.

## Repository structure

```text
.
├── .gitignore
├── README.md
├── TTB_App_Execution_Plan.md
├── ttb-label-verifier/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   ├── models/
│   │   │   ├── rules/
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── frontend/
│   │   ├── src/
│   │   ├── package.json
│   │   └── .env
│   ├── sample_data/
│   └── render.yaml
├── db/
└── README - USAJobs Instructions.md
```

## What the application does

- accepts a manifest and one label image for individual verification
- uses local OpenCV preprocessing and offline EasyOCR
- checks Government Warning presence, casing, and required text
- compares brand name with normalization and fuzzy matching
- checks declared ABV against OCR text on the label
- reports overall status, OCR output, latency, and review recommendation
- accepts ZIP batches containing label images and a manifest
- tracks batch progress and provides CSV export
- allows a reviewer to record APPROVED or REJECTED decisions

## Current verification contract

The backend currently returns a minimal per-check object with a status, for example:

```json
{
  "overall_status": "PASS",
  "flags": [
    {
      "rule": "BRAND_MISMATCH",
      "severity": "FAIL",
      "message": "Expected brand name 'OLD TOM DISTILLERY' not found on label artwork."
    }
  ],
  "checks": {
    "government_warning": { "status": "PASS" },
    "brand_name": { "status": "FAIL_BRAND_MISMATCH" },
    "alcohol_by_volume": { "status": "PASS" }
  }
}
```

This is the schema currently used by the app. Richer fields such as `expected`, `extracted`, and `details` are optional UI metadata rather than required backend contract. The frontend tolerates their absence without breaking the workflow.

## Technology

- Backend: Python, FastAPI, OpenCV, EasyOCR, RapidFuzz, SQLite
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Deployment: Vercel for frontend; Hugging Face Spaces for backend
- OCR: local EasyOCR; no cloud OCR API is required

## Local run instructions

### Backend

From the project directory:

```powershell
cd ttb-label-verifier/backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The backend runs at:

- http://127.0.0.1:8000

Useful endpoints:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

### Frontend

In a second terminal:

```powershell
cd ttb-label-verifier/frontend
npm install
npm run dev
```

Open the local Vite URL shown in the terminal, usually:

- http://localhost:5173

The frontend API URL is configured in `ttb-label-verifier/frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For the deployed Vercel app, the same pattern should point to the direct HF backend URL instead of the spaces landing page.

## Individual review workflow

1. Open the frontend review page.
2. Enter the application ID, brand name, class/type, and ABV.
3. Select a label image.
4. Submit the verification.
5. Review the status badge, checklist, and manual-review recommendation.
6. Record approval or rejection when human judgment is required.

Use simple values such as `45%` in the manifest field to keep verification cases straightforward.

## Batch workflow

A batch ZIP should contain:

```text
manifest.json
COLA-2026-001.png
COLA-2026-002.png
...
```

Each manifest entry should contain the application fields at the top level:

```json
{
  "application_id": "COLA-2026-001",
  "brand_name": "OLD TOM DISTILLERY",
  "class_type": "Kentucky Straight Bourbon Whiskey",
  "alcohol_by_volume": "45%",
  "net_contents": "750 mL"
}
```

The image filename without its extension should match `application_id`. Upload the ZIP on the Batch Queue page, wait for processing to finish, review the summary output, and export the CSV report. If needed, use `ttb-label-verifier\sample_data\test1.zip` as a reference example.

The synthetic fixtures can be regenerated from the repository root:

```powershell
python sample_data\generate_mock_labels.py
```

## Benchmark

Run the benchmark from the repository root:

```powershell
python backend\benchmark_phase5.py --limit 20 --output backend\benchmark.json
```

The report includes fixture accuracy, per-image latency, preprocessing and OCR timing, and functional failures.

## Known limitations

- the environment uses CPU-only PyTorch; CUDA and an NVIDIA GPU were not available
- EasyOCR is accurate on the synthetic corpus but can take several seconds per image on personal hardware
- Tesseract was tested as an alternative, but its synthetic accuracy was too low to be the primary engine
- the dataset is synthetic and not representative of all real label photographs
- OCR confidence is not a guarantee of correctness
- the prototype does not include authentication, production retention, COLA integration, or formal regulatory approval

## Future work

The next logical enhancement is a confidence rating model that quantifies the reliability of each verification result. This rating could be based on OCR confidence, rule certainty, image quality signal, and a fuzzy-match quality score.

The goal would be to estimate whether a result is:

- high confidence: auto-approve or auto-reject without human review
- medium confidence: require supervisor review
- low confidence: escalate to human inspection before any decision

This would provide a structured decision support layer to inform whether further human approval is necessary.

## Disclaimer

This software was created solely as a job-application prototype and demonstration of engineering approach. It must not be used for formal regulatory review, business operations, professional services, production workloads, compliance determinations, or any decision affecting applicants or organizations. Results require human validation and should not be treated as authoritative.
