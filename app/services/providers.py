from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import uuid
from pathlib import Path

import httpx

from app.schemas import ProductExecutionStatus, ProductRow, VideoConfig
from app.services.asset_library import AssetLibraryService
from app.services.prompt_builder import build_prompt
from app.settings import Settings


class LLMProvider:
    async def generate_prompt(self, product: ProductRow, config: VideoConfig) -> str:
        raise NotImplementedError


class SeedanceProvider:
    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    async def generate_prompt(self, product: ProductRow, config: VideoConfig) -> str:
        await asyncio.sleep(0.15)
        return build_prompt(product, config)


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_prompt(self, product: ProductRow, config: VideoConfig) -> str:
        fallback_prompt = build_prompt(product, config)
        if not self.settings.llm_api_base or not self.settings.llm_api_key:
            return fallback_prompt

        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You write production-ready prompts for ecommerce video generation. Never leave placeholders unresolved.",
                },
                {"role": "user", "content": fallback_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class MockSeedanceProvider(SeedanceProvider):
    def __init__(self, videos_dir: Path, model_name: str) -> None:
        self.videos_dir = videos_dir
        self.model_name = model_name

    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        await asyncio.sleep(0.35)
        artifact_path = self.videos_dir / f"{product.id}.json"
        artifact = {
            "mode": "mock",
            "model": self.model_name,
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.product_name,
            "prompt": prompt,
            "config": config.model_dump(),
            "product_assets": product_assets,
            "human_model_assets": model_assets,
            "batch_reference_images": batch_reference_images,
            "batch_reference_videos": batch_reference_videos,
            "audio_files": audio_files,
        }
        artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        return {
            "provider_job_id": str(uuid.uuid4()),
            "output_path": str(artifact_path),
            "download_url": None,
            "status": "completed",
        }


class HTTPSeedanceProvider(SeedanceProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.asset_library = AssetLibraryService(settings)
        base_url = settings.ark_api_base or settings.seedance_api_base
        if not settings.seedance_api_key:
            raise RuntimeError("Seedance credentials are not configured.")
        try:
            from byteplussdkarkruntime import Ark
        except ImportError as exc:  # pragma: no cover - guarded for environments without live SDK deps
            raise RuntimeError("byteplus-python-sdk-v2 is required for live Seedance generation.") from exc

        self.client = Ark(api_key=settings.seedance_api_key, base_url=base_url) if base_url else Ark(
            api_key=settings.seedance_api_key
        )

    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        resolved_model_assets = [await self.asset_library.ensure_reference_image_asset(asset) for asset in model_assets]
        reference_images = [value for value in [*product_assets, *resolved_model_assets, *batch_reference_images] if value]
        reference_videos = [value for value in batch_reference_videos if value]
        reference_audio = [value for value in audio_files if value]
        ratio_map = {
            "16:9": "16:9",
            "9:16": "9:16",
            "1:1": "1:1",
            "4:3": "4:3",
            "3:4": "3:4",
            "21:9": "21:9",
        }
        ratio = ratio_map.get(config.aspect_ratio, "16:9")
        content_items = _build_seedance_content(
            prompt=prompt,
            reference_images=reference_images,
            reference_videos=reference_videos,
            reference_audio=reference_audio,
        )

        payload = {
            "model": self.settings.seedance_model,
            "content": content_items,
            "generate_audio": config.sound_required,
            "ratio": ratio,
            "duration": config.duration_seconds,
            "resolution": config.resolution,
            "watermark": False,
        }
        task_response = await self._create_task_with_asset_retry(payload)
        task_data = task_response.model_dump() if hasattr(task_response, "model_dump") else json.loads(task_response.to_json())
        task_id = str(task_data.get("id") or task_data.get("task_id") or task_data.get("job_id") or uuid.uuid4())
        final_data = await self._wait_for_task(task_id)
        final_status = str(final_data.get("status") or "").lower()
        if final_status != "succeeded":
            error_message = None
            if isinstance(final_data.get("error"), dict):
                error_message = final_data["error"].get("message")
            raise RuntimeError(error_message or f"Seedance task ended with status: {final_status or 'unknown'}")

        content = final_data.get("content") if isinstance(final_data.get("content"), dict) else {}
        download_url = content.get("video_url") or content.get("file_url") or content.get("last_frame_url")
        usage = final_data.get("usage") if isinstance(final_data.get("usage"), dict) else {}
        token_consumption = _extract_token_consumption(usage)
        token_unit_price = _seedance_token_unit_price_per_million(
            resolution=config.resolution,
            includes_input_video=bool(reference_videos),
        )
        estimated_price_usd = _estimate_price_usd(token_unit_price, token_consumption)

        return {
            "provider_job_id": task_id,
            "output_path": None,
            "download_url": download_url,
            "token_consumption": token_consumption,
            "token_unit_price_per_million": token_unit_price,
            "estimated_price_usd": estimated_price_usd,
            "status": "completed",
        }

    async def _wait_for_task(self, task_id: str) -> dict[str, object]:
        delay_seconds = max(1, self.settings.seedance_poll_interval_seconds)
        timeout_seconds = max(delay_seconds, self.settings.seedance_timeout_seconds)
        max_attempts = max(1, (timeout_seconds + delay_seconds - 1) // delay_seconds)
        for _ in range(max_attempts):
            task = await asyncio.to_thread(self.client.content_generation.tasks.get, task_id=task_id)
            data = task.model_dump() if hasattr(task, "model_dump") else json.loads(task.to_json())
            status = str(data.get("status") or "").lower()
            if status in {"succeeded", "failed", "cancelled"}:
                return data
            await asyncio.sleep(delay_seconds)

        raise RuntimeError(
            f"Seedance task timed out before completion after waiting {timeout_seconds} seconds."
        )

    async def _create_task_with_asset_retry(self, payload: dict[str, object]) -> object:
        max_attempts = 12
        delay_seconds = 10
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                return await asyncio.to_thread(self.client.content_generation.tasks.create, **payload)
            except Exception as exc:  # noqa: BLE001
                if not _is_asset_processing_error(exc) or attempt == max_attempts - 1:
                    raise
                last_error = exc
                await asyncio.sleep(delay_seconds)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Unable to create Seedance task.")


def _to_ark_asset_url(reference: str) -> str:
    if reference.startswith(("http://", "https://", "data:")):
        return reference

    path = Path(reference)
    if not path.exists():
        return reference

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_seedance_content(
    *,
    prompt: str,
    reference_images: list[str],
    reference_videos: list[str],
    reference_audio: list[str],
) -> list[dict[str, object]]:
    content_items: list[dict[str, object]] = [{"type": "text", "text": prompt}]
    for image_reference in reference_images:
        content_items.append(
            {
                "type": "image_url",
                "image_url": {"url": _to_ark_asset_url(image_reference)},
                "role": "reference_image",
            }
        )
    for video_reference in reference_videos:
        content_items.append(
            {
                "type": "video_url",
                "video_url": {"url": _to_ark_asset_url(video_reference)},
                "role": "reference_video",
            }
        )
    for audio_reference in reference_audio:
        content_items.append(
            {
                "type": "audio_url",
                "audio_url": {"url": _to_ark_asset_url(audio_reference)},
                "role": "reference_audio",
            }
        )
    return content_items


def _is_asset_processing_error(error: Exception) -> bool:
    message = str(error).lower()
    return "asset is still processing" in message or "not available yet" in message


def _extract_token_consumption(usage: dict[str, object]) -> int | None:
    for key in ("total_tokens", "completion_tokens", "tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
    return None


def _seedance_token_unit_price_per_million(*, resolution: str, includes_input_video: bool) -> float | None:
    _ = resolution
    return 4.3 if includes_input_video else 7.0


def _estimate_price_usd(token_unit_price_per_million: float | None, token_consumption: int | None) -> float | None:
    if token_unit_price_per_million is None or token_consumption is None:
        return None
    return round(token_unit_price_per_million * token_consumption / 1_000_000, 6)


def build_providers(settings: Settings) -> tuple[LLMProvider, SeedanceProvider]:
    if settings.llm_mode == "live":
        llm_provider: LLMProvider = OpenAICompatibleLLMProvider(settings)
    else:
        llm_provider = MockLLMProvider()

    if settings.seedance_mode == "live":
        seedance_provider: SeedanceProvider = HTTPSeedanceProvider(settings)
    else:
        seedance_provider = MockSeedanceProvider(settings.videos_dir, settings.seedance_model)

    return llm_provider, seedance_provider
