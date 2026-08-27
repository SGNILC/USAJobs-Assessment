# TTB Label Verification Prototype

## Purpose

This project is a standalone prototype for automating the review of alcohol beverage labels against application metadata. It performs comparisons—such as brand name, class/type, alcohol by volume (ABV), and the required Government Warning statement—while keeping final judgment for a human reviewer.

It is built using local Python tooling and a React frontend, the system demonstrates an offline, end-to-end workflow encompassing:

* Image upload
* Local OCR extraction
* Rule-based compliance checks for brand, class/type, ABV, and government warnings
* Batch processing capabilities
* A manual review interface for final decisions

Note: This Developed strictly for demonstration and internal review, the prototype is not intended for formal regulatory decisions, business operations, professional use, production deployment, or integration with the TTB COLA system. Known edge cases and technical limitations are documented in the project README.

## Repository structure

```text
ttb-label-verifier/
├── backend/
│   ├── app/
│   │   ├── core/         # OCR, image preprocessing, batch processing
│   │   ├── models/       # SQLite helpers and persistence
│   │   ├── rules/        # TTB compliance logic
│   │   └── main.py       # FastAPI endpoints
│   ├── tests/            # validation and smoke tests
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
├── db/
└── ttb-label-verifier/
```

## What the application does

- Accepts a manifest and one label image for individual verification
- Uses local OpenCV preprocessing and offline EasyOCR
- Checks Government Warning presence, casing, and required text
- Compares brand name with normalization and fuzzy matching
- Checks the declared ABV against OCR text on the label
- Reports overall status, OCR text, latency, and manual-review recommendation
- Accepts ZIP batches containing label images and a manifest
- Tracks batch progress and provides CSV export
- Allows an inspector to record an APPROVED or REJECTED manual decision

## Current verification data contract

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

This is the schema currently used by the app. Richer fields like `expected`, `extracted`, and `details` are optional UI metadata rather than a required backend contract. The frontend is written to render them when they exist, but it must safely tolerate missing values.

## Technology

- Backend: Python, FastAPI, OpenCV, EasyOCR, RapidFuzz, SQLite
- Frontend: React, TypeScript, Vite, Tailwind CSS
- OCR: Local EasyOCR; no cloud OCR API is required

## Run locally

### Backend

From the `ttb-label-verifier` directory:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

Useful endpoints:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

The frontend API URL is configured in `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Restart Vite after changing this value.

## Individual review workflow

1. Open the frontend review page.
2. Enter the application ID, brand name, class/type, and ABV.
3. Select a label image.
4. Submit the verification.
5. Review the status badge, checklist, and manual-review recommendation.
6. Record an approval or rejection when human judgment is required.

Use simple ABV values such as `45%` in the manifest field.

## Batch workflow

A batch ZIP should contain:

```text
manifest.json
COLA-2026-001.png
COLA-2026-002.png
...
```

Each manifest entry must contain application fields at the top level:

```json
{
  "application_id": "COLA-2026-001",
  "brand_name": "OLD TOM DISTILLERY",
  "class_type": "Kentucky Straight Bourbon Whiskey",
  "alcohol_by_volume": "45%",
  "net_contents": "750 mL"
}
```

The image filename without its extension must match `application_id`. Upload the ZIP on the Batch Queue page, wait for completion, review the job summary, and export the CSV report.

The synthetic fixtures can be regenerated from the repository root:

```powershell
.\backend\venv\Scripts\python.exe sample_data\generate_mock_labels.py
```

## Benchmark

Run the benchmark from the repository root:

```powershell
.\backend\venv\Scripts\python.exe backend\benchmark_phase5.py --limit 20 --output backend\benchmark.json
```

The report includes fixture accuracy, per-image latency, preprocessing and OCR timing, and functional failures.

The best recorded EasyOCR run matched 19 of 20 synthetic fixtures, or 95% accuracy. Mean latency was approximately 4.54 seconds on an otherwise idle laptop, although several individual images exceeded five seconds.

## Known limitations

- The environment uses CPU-only PyTorch (`2.13.0+cpu`); CUDA and an NVIDIA GPU were not available.
- EasyOCR is accurate on the synthetic corpus but commonly takes about 5–8 seconds per image on personal hardware.
- Tesseract was tested as an alternative and was faster, but its synthetic accuracy was too low to be the primary engine.
- The 1024-pixel image test reduced accuracy further; the working image limit remains 1280 pixels.
- The dataset is synthetic and is not representative of all real label photographs.
- The OCR confidence signal is not a guarantee of correctness.
- GPU performance and sustained throughput for larger batches were not validated.
- The prototype has no authentication, production retention policy, COLA integration, or formal regulatory approval.

## Disclaimer

This software was created solely as a job-application prototype and demonstration of engineering approach. It must not be used for formal regulatory review, business operations, professional services, production workloads, compliance determinations, or any decision affecting applicants or organizations. Results require human validation and should not be treated as authoritative.
