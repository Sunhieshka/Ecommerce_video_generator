from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from app.db import connect, init_db
from app.repository import JobRepository
from app.schemas import CreateJobResponse, RegenerateProductRequest, VideoConfig
from app.services.excel_parser import parse_excel
from app.services.job_runner import JobRunner
from app.services.providers import build_providers
from app.settings import Settings


def parse_config(raw_config: str) -> VideoConfig:
    try:
        payload = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid config payload") from exc
    merged_payload = {
        "style": "cinematic",
        "duration_seconds": 8,
        "resolution": "1080p",
        "aspect_ratio": "9:16",
        "tone_override": None,
        "sound_required": True,
        **payload,
    }
    return VideoConfig(**merged_payload)


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    settings = custom_settings or Settings.from_env()
    settings.ensure_directories()
    init_db(settings.db_path)
    connection = connect(settings.db_path)
    llm_provider, seedance_provider = build_providers(settings)
    job_runner = JobRunner(connection=connection, llm_provider=llm_provider, seedance_provider=seedance_provider)

    web_app = FastAPI(title="Ecommerce Video Generator", version="0.1.0")
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    web_app.state.settings = settings
    web_app.state.connection = connection
    web_app.state.job_runner = job_runner
    register_routes(web_app)
    return web_app


def register_routes(app: FastAPI) -> None:
    @app.get("/")
    async def home() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=302)

    @app.post("/api/jobs", response_model=CreateJobResponse)
    async def create_job(
        request: Request,
        file: UploadFile = File(...),
        config_json: str = Form(...),
    ) -> CreateJobResponse:
        settings: Settings = request.app.state.settings
        config = parse_config(config_json)
        upload_path = settings.uploads_dir / file.filename
        with upload_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        try:
            parsed = parse_excel(upload_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        repository = JobRepository(request.app.state.connection)
        job_id = repository.create_job(
            filename=file.filename,
            config=config,
            rows=parsed.rows,
            concurrency_limit=settings.max_concurrent_products,
        )
        request.app.state.job_runner.schedule(job_id, config)

        return CreateJobResponse(
            job_id=job_id,
            accepted_products=len(parsed.rows),
            rejected_products=max(len(parsed.warnings), 0),
            concurrency_limit=settings.max_concurrent_products,
            status="running",
        )

    @app.get("/api/jobs/{job_id}")
    async def get_job(request: Request, job_id: str) -> JSONResponse:
        repository = JobRepository(request.app.state.connection)
        job = repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JSONResponse(job.model_dump())

    @app.get("/api/jobs/{job_id}/products")
    async def get_products(request: Request, job_id: str) -> JSONResponse:
        repository = JobRepository(request.app.state.connection)
        products = repository.list_products(job_id)
        return JSONResponse([item.model_dump() for item in products])

    @app.post("/api/jobs/{job_id}/retry")
    async def retry_failed_products(request: Request, job_id: str) -> JSONResponse:
        repository = JobRepository(request.app.state.connection)
        job = repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        products = repository.list_products(job_id)
        failed = [item for item in products if item.status == "failed"]
        if not failed:
            return JSONResponse({"message": "No failed products found.", "retried": 0})

        for item in failed:
            repository.update_product_status(item.id, "queued", error_message=None)

        config = VideoConfig(
            style=job.style,
            duration_seconds=job.duration_seconds,
            resolution=job.resolution,
            aspect_ratio=job.aspect_ratio,
            tone_override=job.tone_override,
            sound_required=job.sound_required,
        )
        request.app.state.job_runner.schedule(job_id, config)
        return JSONResponse({"message": "Retry started", "retried": len(failed)})

    @app.post("/api/jobs/{job_id}/products/{product_id}/regenerate")
    async def regenerate_product(
        request: Request,
        job_id: str,
        product_id: str,
        payload: RegenerateProductRequest,
    ) -> JSONResponse:
        repository = JobRepository(request.app.state.connection)
        job = repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        product = repository.get_product(job_id, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        if request.app.state.job_runner.is_product_running(job_id, product_id):
            raise HTTPException(status_code=409, detail="This product is already generating.")

        config = VideoConfig(
            style=job.style,
            duration_seconds=job.duration_seconds,
            resolution=job.resolution,
            aspect_ratio=job.aspect_ratio,
            tone_override=job.tone_override,
            sound_required=job.sound_required,
        )
        request.app.state.job_runner.schedule_product_regeneration(
            job_id=job_id,
            product_id=product_id,
            config=config,
            prompt=payload.prompt.strip(),
        )
        return JSONResponse({"message": "Product regeneration started", "product_id": product_id})

    @app.get("/api/jobs/{job_id}/download/{product_id}")
    async def download_video(request: Request, job_id: str, product_id: str) -> FileResponse:
        repository = JobRepository(request.app.state.connection)
        products = repository.list_products(job_id)
        product = next((item for item in products if item.id == product_id), None)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if not product.output_path:
            raise HTTPException(status_code=404, detail="Output file is not ready")
        path = Path(product.output_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Output file path does not exist")
        return FileResponse(path=path, media_type="application/octet-stream", filename=path.name)


app = create_app()
