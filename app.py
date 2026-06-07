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


from config import DEFAULT_OUTPUT
OUTPUT_DIR = Path(DEFAULT_OUTPUT)
OUTPUT_DIR.mkdir(exist_ok=True)

PROJECT_DIR = Path(__file__).parent

app.mount("/site", StaticFiles(directory=str(OUTPUT_DIR), html=True), name="site")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR), html=True), name="output")


@app.get("/methodology")
def get_methodology():
    path = PROJECT_DIR / "methodology" / "README.md"
    content = path.read_text(encoding="utf-8")
    import markdown
    html = markdown.markdown(content, extensions=["fenced_code", "tables"])
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>笔记方法论 — ink</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#c4c4cf;max-width:800px;margin:0 auto;padding:40px 24px;line-height:1.8}}
h1{{color:#ffd700;font-size:2rem;border-bottom:1px solid #2a2a3a;padding-bottom:8px}}
h2{{color:#ffd700;font-size:1.3rem;margin-top:32px}}
h3{{color:#e0e0e8;font-size:1.1rem;margin-top:24px}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{border:1px solid #2a2a3a;padding:8px 12px;text-align:left;font-size:.9rem}}
th{{background:#1a1a26;color:#ffd700}}
code{{background:#1a1a26;padding:2px 6px;border-radius:4px;font-size:.85rem}}
blockquote{{border-left:3px solid #ffd700;padding:8px 16px;margin:16px 0;background:#12121a}}
strong{{color:#ffd700}}
a{{color:#ffd700}}
.back{{margin-bottom:24px;display:inline-block;color:#888;text-decoration:none}}
.back:hover{{color:#ffd700}}
hr{{border:none;border-top:1px solid #2a2a3a;margin:24px 0}}
</style>
</head>
<body><a href="/" class="back">&larr; 返回</a>
{html}
</body></html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(page)


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("INK_PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
