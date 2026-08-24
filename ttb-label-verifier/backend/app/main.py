import json
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.preprocess import extract_text_from_image
from app.rules.checker import verify_label_compliance
from app.models.db import init_db, log_verification, get_batch_job, save_decision, get_decision
from app.core.batch import process_batch_zip, generate_batch_csv, executor

app = FastAPI(
    title="TTB Label Verification Engine",
    version="1.0.0",
    description="Automated compliance engine for COLA label validation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "EasyOCR + OpenCV"}

@app.post("/api/v1/verify")
async def verify_label(
    file: UploadFile = File(...),
    manifest: str = Form(...)
):
    try:
        manifest_data = json.loads(manifest)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format in manifest payload.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    start_time = time.time()
    ocr_extracted_text = extract_text_from_image(image_bytes)
    verification_results = verify_label_compliance(ocr_extracted_text, manifest_data)
    latency = round(time.time() - start_time, 2)

    app_id = manifest_data.get("application_id", "UNKNOWN")
    log_verification(app_id, verification_results.get("overall_status"), latency, verification_results)

    return {
        "application_id": app_id,
        "latency_seconds": latency,
        "verification_result": verification_results,
        "raw_ocr_extracted": ocr_extracted_text
    }

@app.post("/api/v1/verify/batch")
async def verify_batch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Batch upload must be a .zip file.")

    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    zip_bytes = await file.read()
    
    background_tasks.add_task(process_batch_zip, zip_bytes, job_id)
    
    return {
        "job_id": job_id,
        "status": "PROCESSING",
        "message": "Batch verification initiated in background."
    }

@app.get("/api/v1/batch/{job_id}")
def get_batch_status(job_id: str):
    job = get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job ID not found.")
    return job

@app.get("/api/v1/batch/{job_id}/export")
def export_batch_csv(job_id: str):
    job = get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job ID not found.")
    
    csv_data = generate_batch_csv(job.get("summary", {}))
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ttb_batch_{job_id}_export.csv"}
    )


class DecisionPayload(BaseModel):
    decision: str
    notes: str | None = None


@app.post("/api/v1/verify/{application_id}/decision")
def submit_decision(application_id: str, payload: DecisionPayload):
    if payload.decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="decision must be 'APPROVED' or 'REJECTED'.")
    save_decision(application_id, payload.decision, payload.notes)
    return {"application_id": application_id, "decision": payload.decision, "notes": payload.notes}


@app.get("/api/v1/verify/{application_id}/decision")
def read_decision(application_id: str):
    decision = get_decision(application_id)
    if not decision:
        raise HTTPException(status_code=404, detail="No decision recorded for this application ID.")
    return decision