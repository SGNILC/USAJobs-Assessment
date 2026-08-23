import sqlite3
import json
from datetime import datetime

DB_PATH = "ttb_audit.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Audit log table for individual label verifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT,
            status TEXT,
            latency_seconds REAL,
            results_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tracking table for asynchronous batch processing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            job_id TEXT PRIMARY KEY,
            total_items INTEGER,
            processed_items INTEGER DEFAULT 0,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            summary_json TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def log_verification(application_id: str, status: str, latency: float, results: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO verification_logs (application_id, status, latency_seconds, results_json) VALUES (?, ?, ?, ?)",
        (application_id, status, latency, json.dumps(results))
    )
    conn.commit()
    conn.close()

def create_batch_job(job_id: str, total_items: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO batch_jobs (job_id, total_items, processed_items, status) VALUES (?, ?, 0, 'PROCESSING')",
        (job_id, total_items)
    )
    conn.commit()
    conn.close()

def update_batch_progress(job_id: str, processed_items: int, total_items: int, summary: dict = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    status = "COMPLETED" if processed_items >= total_items else "PROCESSING"
    summary_str = json.dumps(summary) if summary else None
    cursor.execute(
        "UPDATE batch_jobs SET processed_items = ?, status = ?, summary_json = ? WHERE job_id = ?",
        (processed_items, status, summary_str, job_id)
    )
    conn.commit()
    conn.close()

def get_batch_job(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, total_items, processed_items, status, summary_json FROM batch_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "job_id": row[0],
            "total_items": row[1],
            "processed_items": row[2],
            "status": row[3],
            "summary": json.loads(row[4]) if row[4] else {}
        }
    return None