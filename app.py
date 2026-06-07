import os
import json
import uuid
import shutil
from pathlib import Path
from threading import Thread
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from pipeline import Pipeline

app = FastAPI(title="ink - knowledge note")

JOBS = {}
MAX_CONCURRENT = 2
STATIC_DIR = Path(__file__).parent / "static"
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    subtitle: UploadFile = File(None),
    api_key: str = Form(None),
    api_base: str = Form(None),
    model: str = Form("glm-4-flash"),
    use_llm: bool = Form(True),
):
    running = sum(1 for j in JOBS.values() if j["status"] in ("queued", "running"))
    if running >= MAX_CONCURRENT:
        raise HTTPException(429, "Too many concurrent jobs (max 2)")

    job_id = uuid.uuid4().hex[:8]
    ext = Path(file.filename).suffix.lower()
    src_path = TEMP_DIR / f"{job_id}{ext}"
    sub_path = None

    with open(src_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if subtitle:
        sub_ext = Path(subtitle.filename).suffix.lower()
        sub_path = TEMP_DIR / f"{job_id}_sub{sub_ext}"
        with open(sub_path, "wb") as f:
            sub_content = await subtitle.read()
            f.write(sub_content)

    key = api_key or os.environ.get("INK_API_KEY")
    JOBS[job_id] = {"status": "queued", "title": Path(file.filename).stem}

    def run_pipeline():
        JOBS[job_id]["status"] = "running"
        try:
            pipe = Pipeline(api_key=key, api_base=api_base, model=model)
            results = pipe.run(src_path, subtitle_path=sub_path, use_llm=use_llm)
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["results"] = results
        except Exception as e:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)
        finally:
            for p in [src_path, sub_path]:
                if p and p.exists():
                    p.unlink()

    Thread(target=run_pipeline, daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/job/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "status": job["status"],
        "title": job.get("title"),
        "error": job.get("error"),
        "results": job.get("results"),
    }


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("INK_PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
