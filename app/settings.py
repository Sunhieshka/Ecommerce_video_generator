from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"
load_dotenv(ROOT_DIR / ".env")


@dataclass
class Settings:
    data_dir: Path
    uploads_dir: Path
    videos_dir: Path
    db_path: Path
    max_concurrent_products: int
    llm_mode: str
    llm_api_base: str | None
    llm_api_key: str | None
    llm_model: str
    llm_provider: str
    seedance_mode: str
    seedance_api_base: str | None
    seedance_api_key: str | None
    seedance_submit_path: str
    seedance_model: str
    ark_api_base: str | None
    max_ref_images: int
    max_ref_videos: int
    max_ref_video_total_duration: int
    max_audio_files: int
    seedance_poll_interval_seconds: int
    seedance_timeout_seconds: int
    byteplus_ak: str | None
    byteplus_sk: str | None
    ark_project_name: str
    ark_region: str
    ark_model_endpoint: str | None
    tos_region: str | None
    tos_bucket_name: str | None
    tos_endpoint: str | None
    tos_presign_expiry_seconds: int
    asset_group_name: str
    asset_group_description: str
    asset_group_cache_path: Path
    asset_cache_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("APP_DATA_DIR", ROOT_DIR / "data")).resolve()
        uploads_dir = data_dir / "uploads"
        videos_dir = data_dir / "videos"
        db_path = Path(os.getenv("APP_DB_PATH", data_dir / "app.db")).resolve()
        llm_api_base = os.getenv("LLM_API_BASE") or os.getenv("ARK_API_BASE") or os.getenv("ARK_BASE_URL")
        llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("ARK_API_KEY")
        ark_api_base = os.getenv("ARK_API_BASE") or os.getenv("ARK_BASE_URL")
        seedance_api_base = os.getenv("SEEDANCE_API_BASE")
        seedance_api_key = os.getenv("SEEDANCE_API_KEY") or os.getenv("ARK_API_KEY")
        byteplus_ak = os.getenv("BYTEPLUS_AK")
        byteplus_sk = os.getenv("BYTEPLUS_SK")
        ark_project_name = os.getenv("ARK_Project", "default")
        ark_region = os.getenv("ARK_REGION", "ap-southeast-1")
        ark_model_endpoint = os.getenv("ARK_Model_endpoint")
        tos_region = os.getenv("TOS_REGION") or os.getenv("tos_region")
        tos_bucket_name = (
            os.getenv("TOS_BUCKET_NAME")
            or os.getenv("TOS_BUSCKET_NAME")
            or os.getenv("tos_buscket_name")
            or os.getenv("TOS_BUCKET")
        )
        tos_endpoint = os.getenv("TOS_ENDPOINT") or (f"tos-{tos_region}.bytepluses.com" if tos_region else None)
        asset_group_name = os.getenv("ARK_ASSET_GROUP_NAME", f"human-model-library-{ark_project_name}")
        asset_group_description = os.getenv(
            "ARK_ASSET_GROUP_DESCRIPTION",
            "Reusable human model image asset group for ecommerce video generation.",
        )
        llm_mode = os.getenv("LLM_MODE") or ("live" if llm_api_key and llm_api_base else "mock")
        seedance_mode = os.getenv("SEEDANCE_MODE") or ("live" if seedance_api_key else "mock")
        return cls(
            data_dir=data_dir,
            uploads_dir=uploads_dir,
            videos_dir=videos_dir,
            db_path=db_path,
            max_concurrent_products=int(os.getenv("MAX_CONCURRENT_PRODUCTS", "5")),
            llm_mode=llm_mode,
            llm_api_base=llm_api_base,
            llm_api_key=llm_api_key,
            llm_model=os.getenv("LLM_MODEL", "seed-2-0-pro-260328"),
            llm_provider=os.getenv("LLM_PROVIDER", "seed"),
            seedance_mode=seedance_mode,
            seedance_api_base=seedance_api_base,
            seedance_api_key=seedance_api_key,
            seedance_submit_path=os.getenv("SEEDANCE_SUBMIT_PATH", "/generate"),
            seedance_model=os.getenv("SEEDANCE_MODEL", "dreamina-seedance-2-0-260128"),
            ark_api_base=ark_api_base,
            max_ref_images=int(os.getenv("MAX_REF_IMAGES", "9")),
            max_ref_videos=int(os.getenv("MAX_REF_VIDEOS", "3")),
            max_ref_video_total_duration=int(os.getenv("MAX_REF_VIDEO_TOTAL_DURATION", "15")),
            max_audio_files=int(os.getenv("MAX_AUDIO_FILES", "3")),
            seedance_poll_interval_seconds=int(os.getenv("SEEDANCE_POLL_INTERVAL_SECONDS", "10")),
            seedance_timeout_seconds=int(os.getenv("SEEDANCE_TIMEOUT_SECONDS", "1800")),
            byteplus_ak=byteplus_ak,
            byteplus_sk=byteplus_sk,
            ark_project_name=ark_project_name,
            ark_region=ark_region,
            ark_model_endpoint=ark_model_endpoint,
            tos_region=tos_region,
            tos_bucket_name=tos_bucket_name,
            tos_endpoint=tos_endpoint,
            tos_presign_expiry_seconds=int(os.getenv("TOS_PRESIGN_EXPIRY_SECONDS", "86400")),
            asset_group_name=asset_group_name,
            asset_group_description=asset_group_description,
            asset_group_cache_path=(data_dir / "ark_asset_group.json").resolve(),
            asset_cache_path=(data_dir / "ark_asset_cache.json").resolve(),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
