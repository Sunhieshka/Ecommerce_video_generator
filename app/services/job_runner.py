from __future__ import annotations

import asyncio
import sqlite3

from app.repository import JobRepository
from app.schemas import ProductRow, VideoConfig
from app.services.providers import LLMProvider, SeedanceProvider


class JobRunner:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.active_jobs: set[str] = set()
        self.active_products: set[tuple[str, str]] = set()

    def is_running(self, job_id: str) -> bool:
        return job_id in self.active_jobs

    def schedule(self, job_id: str, config: VideoConfig, llm_provider: LLMProvider, seedance_provider: SeedanceProvider) -> None:
        if job_id in self.active_jobs:
            return
        self.active_jobs.add(job_id)
        asyncio.create_task(self._run_job(job_id, config, llm_provider, seedance_provider))

    def is_product_running(self, job_id: str, product_id: str) -> bool:
        return (job_id, product_id) in self.active_products

    def schedule_product_regeneration(self, job_id: str, product_id: str, config: VideoConfig, prompt: str, llm_provider: LLMProvider, seedance_provider: SeedanceProvider) -> None:
        key = (job_id, product_id)
        if key in self.active_products:
            return
        self.active_products.add(key)
        asyncio.create_task(self._run_single_product(job_id, product_id, config, llm_provider, seedance_provider, prompt_override=prompt))

    async def _run_job(self, job_id: str, config: VideoConfig, llm_provider: LLMProvider, seedance_provider: SeedanceProvider) -> None:
        repository = JobRepository(self.connection)
        repository.update_job_status(job_id, "running")
        job = repository.get_job(job_id)
        if job is None:
            self.active_jobs.discard(job_id)
            return

        semaphore = asyncio.Semaphore(job.concurrency_limit)
        products = repository.list_products(job_id)

        async def run_product(product_id: str) -> None:
            async with semaphore:
                key = (job_id, product_id)
                self.active_products.add(key)
                try:
                    await self._run_single_product(job_id, product_id, config, llm_provider, seedance_provider)
                finally:
                    self.active_products.discard(key)

        await asyncio.gather(*(run_product(item.id) for item in products))
        self._update_job_completion(repository, job_id)
        self.active_jobs.discard(job_id)

    async def _run_single_product(
        self,
        job_id: str,
        product_id: str,
        config: VideoConfig,
        llm_provider: LLMProvider,
        seedance_provider: SeedanceProvider,
        prompt_override: str | None = None,
    ) -> None:
        repository = JobRepository(self.connection)
        product = repository.get_product(job_id, product_id)
        if product is None:
            return

        source_product = ProductRow(
            row_number=product.row_number,
            sku=product.sku,
            product_name=product.product_name,
            product_description=product.product_description,
            product_image_refs=repository.list_assets(product.id, "product"),
            human_model_image_refs=repository.list_assets(product.id, "human_model"),
            video_style=product.video_style,
            duration_seconds=product.duration_seconds,
        )
        effective_config = config.model_copy(
            update={
                "style": product.video_style or config.style,
                "duration_seconds": product.duration_seconds or config.duration_seconds,
            }
        )
        batch_reference_images = repository.list_job_assets(job_id, "reference_image")
        batch_reference_videos = repository.list_job_assets(job_id, "reference_video")
        audio_files = repository.list_job_assets(job_id, "audio")

        try:
            repository.update_job_status(job_id, "running")
            if prompt_override is None:
                repository.update_product_status(product.id, "prompt_generating", started=True)
                prompt = await llm_provider.generate_prompt(source_product, effective_config)
            else:
                prompt = prompt_override
            repository.update_product_status(product.id, "prompt_ready", generated_prompt=prompt, error_message=None, started=True)
            repository.update_product_status(product.id, "submitting_to_seedance")
            repository.update_product_status(product.id, "generating_video")

            result = await seedance_provider.generate_video(
                product=product,
                prompt=prompt,
                config=effective_config,
                product_assets=source_product.product_image_refs,
                model_assets=source_product.human_model_image_refs,
                batch_reference_images=batch_reference_images,
                batch_reference_videos=batch_reference_videos,
                audio_files=audio_files,
            )

            repository.add_video_output(
                product_id=product.id,
                provider_job_id=str(result.get("provider_job_id")) if result.get("provider_job_id") else None,
                output_path=str(result.get("output_path")) if result.get("output_path") else None,
                download_url=str(result.get("download_url")) if result.get("download_url") else None,
                token_consumption=int(result["token_consumption"]) if result.get("token_consumption") is not None else None,
                token_unit_price_per_million=(
                    float(result["token_unit_price_per_million"])
                    if result.get("token_unit_price_per_million") is not None
                    else None
                ),
                estimated_price_usd=float(result["estimated_price_usd"]) if result.get("estimated_price_usd") is not None else None,
                status=str(result.get("status") or "completed"),
            )
            repository.update_product_status(product.id, "completed", completed=True)
        except Exception as exc:  # noqa: BLE001
            repository.update_product_status(product.id, "failed", error_message=str(exc), completed=True)
        finally:
            self.active_products.discard((job_id, product_id))
            self._update_job_completion(repository, job_id)

    def _update_job_completion(self, repository: JobRepository, job_id: str) -> None:
        products = repository.list_products(job_id)
        statuses = {item.status for item in products}
        if statuses == {"completed"}:
            repository.update_job_status(job_id, "completed")
            return
        if statuses.issubset({"completed", "failed"}):
            repository.update_job_status(job_id, "completed_with_errors")
            return
        repository.update_job_status(job_id, "running")
