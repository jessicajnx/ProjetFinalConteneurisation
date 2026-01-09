import os
import json
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


def get_redis_client() -> redis.Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


app = FastAPI(title="Projet Final Conteneurisation - API", version="1.0.0")


class JobRequest(BaseModel):
    text: str


@app.get("/healthz")
def healthz():
    try:
        r = get_redis_client()
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "detail": str(e)})


@app.post("/jobs")
def create_job(req: JobRequest):
    r = get_redis_client()
    job_id = uuid.uuid4().hex
    job_key_status = f"job:{job_id}:status"
    job_key_result = f"job:{job_id}:result"

    r.set(job_key_status, "queued", ex=3600)
    payload = {"id": job_id, "text": req.text}
    r.rpush("jobs", json.dumps(payload))
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    r = get_redis_client()
    job_key_status = f"job:{job_id}:status"
    job_key_result = f"job:{job_id}:result"

    status: Optional[str] = r.get(job_key_status)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    result = r.get(job_key_result)
    return {"job_id": job_id, "status": status, "result": result}


# Serve a tiny static UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
