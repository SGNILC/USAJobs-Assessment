# TTB Label Verification Prototype

## Purpose

This project is a standalone proof of concept for reviewing alcohol beverage label artwork against application data. It automates routine comparisons for brand name, class/type, alcohol by volume (ABV), and the required Government Warning statement, while leaving final judgment with a human reviewer.

The prototype was created for a job application assessment. It is not intended for formal regulatory decisions, business operations, professional use, production deployment, or integration with the TTB COLA system.

## Repository structure:
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
## What The Application Does

- Accepts an application manifest and one label image for individual verification.
- Uses local OpenCV preprocessing and offline EasyOCR.
- Checks Government Warning presence, casing, and text.
- Compares brand name with normalization and fuzzy matching.
- Checks the declared ABV against text detected on the label.
- Reports overall status, detected text, OCR confidence, latency, image-quality metadata, and manual-review recommendation.
- Accepts ZIP batches containing label images and a `manifest.json` file.
- Tracks batch progress and provides CSV export.
- Allows an inspector to record an APPROVED or REJECTED manual decision.

## Technology

- Backend: Python, FastAPI, OpenCV, EasyOCR, RapidFuzz, SQLite
- Frontend: React, TypeScript, Vite, Tailwind CSS
- OCR: Local EasyOCR; no cloud OCR API is required

## Run Locally

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

## Individual Review Workflow

1. Open the frontend review page.
2. Enter the application ID, brand name, class/type, and ABV.
3. Select a label image.
4. Submit the verification.
5. Review the status badge, checklist, OCR confidence, latency, and manual-review recommendation.
6. Record an approval or rejection when human judgment is required.

Use simple ABV values such as `45%` in the manifest field.

## Batch Workflow

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

The image filename without its extension must match `application_id`. Upload the ZIP on the Batch Queue page, wait for completion, review statuses and confidence values, then export the CSV summary.

The synthetic batch fixtures can be regenerated from the repository root:

```powershell
.\backend\venv\Scripts\python.exe sample_data\generate_mock_labels.py
```

## Benchmark

Run the benchmark from the repository root:

```powershell
.\backend\venv\Scripts\python.exe backend\benchmark_phase5.py --limit 20 --output backend\benchmark.json
```

The report includes fixture accuracy, per-image latency, preprocessing and OCR timing, confidence, and functional failures.

The best recorded EasyOCR run matched 19 of 20 synthetic fixtures, or 95% accuracy. Mean latency was approximately 4.54 seconds on an otherwise idle laptop, although several individual images exceeded five seconds.

## Known Limitations

- The available environment uses CPU-only PyTorch (`2.13.0+cpu`); CUDA and an NVIDIA GPU were not available.
- EasyOCR is accurate on the synthetic corpus but commonly takes about 5-8 seconds per image on this hardware.
- Tesseract was tested as an alternative and was faster, but its measured synthetic-corpus accuracy was only approximately 25-35%, so it is not the primary engine.
- The 1024-pixel image test reduced accuracy to approximately 20-30%; the working image limit is 1280 pixels.
- The dataset is synthetic and is not representative of all real label photographs.
- `COLA-2026-016` demonstrates a quality-detection gap: the combined glare/low-contrast fixture can return `PASS` because measured glare was `0.0` and the current rule requires both glare and low contrast.
- OCR confidence is a recognition signal, not a correctness guarantee.
- GPU performance and sustained throughput for batches of 200-300 labels were not validated.
- The prototype has no authentication, production retention policy, COLA integration, or formal regulatory approval.

## Disclaimer

This software was created solely as a job-application prototype and demonstration of engineering approach. It must not be used for formal regulatory review, business operations, professional services, production workloads, compliance determinations, or any decision affecting applicants or organizations. Results require human validation and should not be treated as authoritative.
