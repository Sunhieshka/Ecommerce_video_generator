from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any

import httpx
from byteplussdkcore.signv4 import SignerV4

from app.settings import Settings


class AssetLibraryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = bool(settings.byteplus_ak and settings.byteplus_sk)

    async def ensure_reference_image_asset(self, reference: str) -> str:
        if not self.enabled or not reference:
            return reference
        if reference.startswith("asset://"):
            return reference

        cache_key = await asyncio.to_thread(self._build_cache_key, reference)
        asset_cache = self._read_json(self.settings.asset_cache_path)
        cached_asset_id = asset_cache.get(cache_key, {}).get("asset_id")
        if cached_asset_id:
            return f"asset://{cached_asset_id}"

        group_id, cache_was_reused = await asyncio.to_thread(self._ensure_group_id)
        source_url = await self._ensure_remote_url(reference)

        try:
            asset_id = await self._create_asset(group_id, source_url)
        except Exception:
            if not cache_was_reused:
                raise
            group_id, _ = await asyncio.to_thread(self._ensure_group_id, True)
            asset_id = await self._create_asset(group_id, source_url)

        asset_cache[cache_key] = {"asset_id": asset_id, "source": reference, "group_id": group_id}
        self._write_json(self.settings.asset_cache_path, asset_cache)
        return f"asset://{asset_id}"

    def _ensure_group_id(self, force_refresh: bool = False) -> tuple[str, bool]:
        cache = self._read_json(self.settings.asset_group_cache_path)
        if not force_refresh and cache.get("group_id"):
            return str(cache["group_id"]), True

        payload = {
            "Name": self.settings.asset_group_name,
            "Description": self.settings.asset_group_description,
            "ProjectName": self.settings.ark_project_name,
        }
        response = self._ark_call("CreateAssetGroup", payload)
        group_id = self._extract_id(response)
        self._write_json(
            self.settings.asset_group_cache_path,
            {
                "group_id": group_id,
                "project_name": self.settings.ark_project_name,
                "region": self.settings.ark_region,
                "name": self.settings.asset_group_name,
            },
        )
        return group_id, False

    async def _ensure_remote_url(self, reference: str) -> str:
        if reference.startswith(("http://", "https://")):
            return reference

        path = Path(reference)
        if not path.exists():
            return reference

        return await asyncio.to_thread(self._upload_to_tos_and_presign, path)

    async def _create_asset(self, group_id: str, url: str) -> str:
        payload = {
            "GroupId": group_id,
            "URL": url,
            "AssetType": "Image",
            "Moderation": {"Strategy": "Skip"},
            "ProjectName": self.settings.ark_project_name,
        }
        response = await asyncio.to_thread(self._ark_call, "CreateAsset", payload)
        return self._extract_id(response)

    def _upload_to_tos_and_presign(self, path: Path) -> str:
        if not self.settings.tos_region or not self.settings.tos_bucket_name or not self.settings.tos_endpoint:
            raise RuntimeError("TOS settings are required to upload local human model images to the asset library.")

        try:
            import tos
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError("The `tos` package is required for uploading local human model images.") from exc

        if not self.settings.byteplus_ak or not self.settings.byteplus_sk:
            raise RuntimeError("BYTEPLUS_AK and BYTEPLUS_SK are required for TOS upload.")

        content_hash = self._hash_file(path)
        extension = path.suffix or mimetypes.guess_extension(mimetypes.guess_type(path.name)[0] or "") or ".bin"
        object_key = f"ark-assets/human-models/{content_hash[:12]}-{uuid.uuid4().hex}{extension}"

        client = tos.TosClientV2(
            self.settings.byteplus_ak,
            self.settings.byteplus_sk,
            self.settings.tos_endpoint,
            self.settings.tos_region,
        )
        with path.open("rb") as file_obj:
            client.put_object(self.settings.tos_bucket_name, object_key, content=file_obj)

        signed = client.pre_signed_url(
            tos.HttpMethodType.Http_Method_Get,
            bucket=self.settings.tos_bucket_name,
            key=object_key,
            expires=self.settings.tos_presign_expiry_seconds,
        )
        return signed.signed_url

    def _ark_call(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.byteplus_ak or not self.settings.byteplus_sk:
            raise RuntimeError("BYTEPLUS_AK and BYTEPLUS_SK are required for ARK asset APIs.")

        host = f"ark.{self.settings.ark_region}.byteplusapi.com"
        query = {"Action": action, "Version": "2024-01-01"}
        headers = {"Host": host, "Content-Type": "application/json; charset=UTF-8"}
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        SignerV4.sign("/", "POST", headers, body, {}, query, self.settings.byteplus_ak, self.settings.byteplus_sk, self.settings.ark_region, "ark")

        response = httpx.post(
            f"https://{host}/",
            params=query,
            headers=headers,
            content=body.encode("utf-8"),
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "Result" in data and isinstance(data["Result"], dict):
            return data["Result"]
        return data

    def _extract_id(self, payload: dict[str, Any]) -> str:
        asset_id = payload.get("Id") or payload.get("id")
        if not asset_id:
            raise RuntimeError(f"ARK asset API did not return an Id field: {payload}")
        return str(asset_id)

    def _build_cache_key(self, reference: str) -> str:
        if reference.startswith(("http://", "https://")):
            return f"url:{reference}"
        path = Path(reference)
        if path.exists():
            return f"sha256:{self._hash_file(path)}"
        return f"raw:{reference}"

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
