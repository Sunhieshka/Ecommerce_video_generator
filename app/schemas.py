from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Resolution = Literal["480p", "720p", "1080p", "4k"]
AspectRatio = Literal["1:1", "4:3", "3:4", "4:5", "9:16", "16:9"]


class VideoConfig(BaseModel):
    style: str = Field(min_length=2, max_length=80)
    duration_seconds: int = Field(ge=3, le=30)
    resolution: Resolution
    aspect_ratio: AspectRatio
    tone_override: str | None = Field(default=None, max_length=200)
    sound_required: bool = True


class ProductRow(BaseModel):
    row_number: int
    sku: str
    product_name: str
    product_description: str
    product_image_refs: list[str]
    human_model_image_refs: list[str]
    video_style: str | None = None
    duration_seconds: int | None = None


class ParsedWorkbook(BaseModel):
    rows: list[ProductRow]
    warnings: list[str]
    columns: list[str]


class CreateJobResponse(BaseModel):
    job_id: str
    accepted_products: int
    rejected_products: int
    concurrency_limit: int
    status: Literal["queued", "running"]


class RegenerateProductRequest(BaseModel):
    prompt: str = Field(min_length=10)


class JobCounts(BaseModel):
    queued: int = 0
    prompt_generating: int = 0
    prompt_ready: int = 0
    submitting_to_seedance: int = 0
    generating_video: int = 0
    completed: int = 0
    failed: int = 0
    validating: int = 0


class JobDetail(BaseModel):
    id: str
    original_filename: str
    status: str
    style: str
    duration_seconds: int
    resolution: str
    aspect_ratio: str
    tone_override: str | None
    sound_required: bool
    concurrency_limit: int
    created_at: str
    updated_at: str
    counts: JobCounts


class ProductExecutionStatus(BaseModel):
    id: str
    job_id: str
    row_number: int
    sku: str
    product_name: str
    product_description: str
    video_style: str | None = None
    duration_seconds: int | None = None
    generated_prompt: str | None = None
    status: str
    error_message: str | None = None
    output_path: str | None = None
    download_url: str | None = None
    token_consumption: int | None = None
    token_unit_price_per_million: float | None = None
    estimated_price_usd: float | None = None
    started_at: str | None = None
    completed_at: str | None = None
