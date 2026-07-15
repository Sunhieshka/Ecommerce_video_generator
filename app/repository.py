from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone

from app.schemas import JobCounts, JobDetail, ProductExecutionStatus, ProductRow, VideoConfig


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class JobRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_job(self, filename: str, config: VideoConfig, rows: list[ProductRow], concurrency_limit: int) -> str:
        job_id = str(uuid.uuid4())
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO jobs (
                id, original_filename, status, style, duration_seconds, resolution,
                aspect_ratio, tone_override, sound_required, concurrency_limit, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                filename,
                "queued",
                config.style,
                config.duration_seconds,
                config.resolution,
                config.aspect_ratio,
                config.tone_override,
                int(config.sound_required),
                concurrency_limit,
                now,
                now,
            ),
        )

        for row in rows:
            product_id = str(uuid.uuid4())
            self.connection.execute(
                """
                INSERT INTO products (
                    id, job_id, row_number, sku, product_name, product_description, video_style, duration_seconds, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    job_id,
                    row.row_number,
                    row.sku,
                    row.product_name,
                    row.product_description,
                    row.video_style,
                    row.duration_seconds,
                    "queued",
                ),
            )
            self._insert_assets(product_id, "product", row.product_image_refs)
            self._insert_assets(product_id, "human_model", row.human_model_image_refs)

        self.connection.commit()
        return job_id

    def _insert_assets(self, product_id: str, asset_type: str, refs: list[str]) -> None:
        for ref in refs:
            self.connection.execute(
                """
                INSERT INTO product_assets (id, product_id, asset_type, source_path, resolved_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), product_id, asset_type, ref, ref),
            )

    def get_job(self, job_id: str) -> JobDetail | None:
        row = self.connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        counts = self.get_job_counts(job_id)
        return JobDetail(
            id=row["id"],
            original_filename=row["original_filename"],
            status=row["status"],
            style=row["style"],
            duration_seconds=row["duration_seconds"],
            resolution=row["resolution"],
            aspect_ratio=row["aspect_ratio"],
            tone_override=row["tone_override"],
            sound_required=bool(row["sound_required"]),
            concurrency_limit=row["concurrency_limit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            counts=counts,
        )

    def get_job_counts(self, job_id: str) -> JobCounts:
        rows = self.connection.execute(
            "SELECT status, COUNT(*) AS count FROM products WHERE job_id = ? GROUP BY status", (job_id,)
        ).fetchall()
        mapping = {row["status"]: row["count"] for row in rows}
        return JobCounts(
            queued=mapping.get("queued", 0),
            validating=mapping.get("validating", 0),
            prompt_generating=mapping.get("prompt_generating", 0),
            prompt_ready=mapping.get("prompt_ready", 0),
            submitting_to_seedance=mapping.get("submitting_to_seedance", 0),
            generating_video=mapping.get("generating_video", 0),
            completed=mapping.get("completed", 0),
            failed=mapping.get("failed", 0),
        )

    def list_products(self, job_id: str) -> list[ProductExecutionStatus]:
        rows = self.connection.execute(
            "SELECT * FROM products WHERE job_id = ? ORDER BY row_number ASC", (job_id,)
        ).fetchall()
        items: list[ProductExecutionStatus] = []
        for row in rows:
            output = self.connection.execute(
                "SELECT * FROM video_outputs WHERE product_id = ? ORDER BY rowid DESC LIMIT 1", (row["id"],)
            ).fetchone()
            items.append(
                ProductExecutionStatus(
                    id=row["id"],
                    job_id=row["job_id"],
                    row_number=row["row_number"],
                    sku=row["sku"],
                    product_name=row["product_name"],
                    product_description=row["product_description"],
                    video_style=row["video_style"],
                    duration_seconds=row["duration_seconds"],
                    generated_prompt=row["generated_prompt"],
                    status=row["status"],
                    error_message=row["error_message"],
                    output_path=output["output_path"] if output else None,
                    download_url=output["download_url"] if output else None,
                    token_consumption=output["token_consumption"] if output else None,
                    token_unit_price_per_million=output["token_unit_price_per_million"] if output else None,
                    estimated_price_usd=output["estimated_price_usd"] if output else None,
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                )
            )
        return items

    def get_product(self, job_id: str, product_id: str) -> ProductExecutionStatus | None:
        row = self.connection.execute(
            "SELECT * FROM products WHERE job_id = ? AND id = ? LIMIT 1",
            (job_id, product_id),
        ).fetchone()
        if row is None:
            return None
        output = self.connection.execute(
            "SELECT * FROM video_outputs WHERE product_id = ? ORDER BY rowid DESC LIMIT 1", (row["id"],)
        ).fetchone()
        return ProductExecutionStatus(
            id=row["id"],
            job_id=row["job_id"],
            row_number=row["row_number"],
            sku=row["sku"],
            product_name=row["product_name"],
            product_description=row["product_description"],
            video_style=row["video_style"],
            duration_seconds=row["duration_seconds"],
            generated_prompt=row["generated_prompt"],
            status=row["status"],
            error_message=row["error_message"],
            output_path=output["output_path"] if output else None,
            download_url=output["download_url"] if output else None,
            token_consumption=output["token_consumption"] if output else None,
            token_unit_price_per_million=output["token_unit_price_per_million"] if output else None,
            estimated_price_usd=output["estimated_price_usd"] if output else None,
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def list_assets(self, product_id: str, asset_type: str) -> list[str]:
        rows = self.connection.execute(
            "SELECT resolved_path FROM product_assets WHERE product_id = ? AND asset_type = ?",
            (product_id, asset_type),
        ).fetchall()
        return [str(row["resolved_path"]) for row in rows]

    def add_job_asset(
        self,
        job_id: str,
        asset_type: str,
        source_path: str,
        duration_seconds: float | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO job_assets (id, job_id, asset_type, source_path, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), job_id, asset_type, source_path, duration_seconds),
        )
        self.connection.commit()

    def list_job_assets(self, job_id: str, asset_type: str) -> list[str]:
        rows = self.connection.execute(
            "SELECT source_path FROM job_assets WHERE job_id = ? AND asset_type = ? ORDER BY rowid ASC",
            (job_id, asset_type),
        ).fetchall()
        return [str(row["source_path"]) for row in rows]

    def update_product_status(
        self,
        product_id: str,
        status: str,
        generated_prompt: str | None = None,
        error_message: str | None = None,
        started: bool = False,
        completed: bool = False,
    ) -> None:
        now = utc_now()
        set_fragments = ["status = ?", "error_message = ?"]
        values: list[object] = [status, error_message]
        if generated_prompt is not None:
            set_fragments.append("generated_prompt = ?")
            values.append(generated_prompt)
        if started:
            set_fragments.append("started_at = ?")
            values.append(now)
        if completed:
            set_fragments.append("completed_at = ?")
            values.append(now)

        values.append(product_id)
        self.connection.execute(
            f"UPDATE products SET {', '.join(set_fragments)} WHERE id = ?",
            tuple(values),
        )
        self.connection.commit()

    def add_video_output(
        self,
        product_id: str,
        provider_job_id: str | None,
        output_path: str | None,
        download_url: str | None,
        token_consumption: int | None,
        token_unit_price_per_million: float | None,
        estimated_price_usd: float | None,
        status: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO video_outputs (
                id, product_id, provider_job_id, output_path, download_url,
                token_consumption, token_unit_price_per_million, estimated_price_usd, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                product_id,
                provider_job_id,
                output_path,
                download_url,
                token_consumption,
                token_unit_price_per_million,
                estimated_price_usd,
                status,
            ),
        )
        self.connection.commit()

    def update_job_status(self, job_id: str, status: str) -> None:
        self.connection.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, utc_now(), job_id),
        )
        self.connection.commit()
