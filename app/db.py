from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                status TEXT NOT NULL,
                style TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                resolution TEXT NOT NULL,
                aspect_ratio TEXT NOT NULL,
                tone_override TEXT,
                sound_required INTEGER NOT NULL DEFAULT 1,
                concurrency_limit INTEGER NOT NULL DEFAULT 5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                row_number INTEGER NOT NULL,
                sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_description TEXT NOT NULL,
                video_style TEXT,
                duration_seconds INTEGER,
                generated_prompt TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                started_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS product_assets (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES products(id),
                asset_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                resolved_path TEXT
            );

            CREATE TABLE IF NOT EXISTS video_outputs (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL REFERENCES products(id),
                provider_job_id TEXT,
                output_path TEXT,
                download_url TEXT,
                token_consumption INTEGER,
                token_unit_price_per_million REAL,
                estimated_price_usd REAL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_assets (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                asset_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                duration_seconds REAL
            );

            CREATE INDEX IF NOT EXISTS idx_products_job_id ON products(job_id);
            CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
            CREATE INDEX IF NOT EXISTS idx_video_outputs_product_id ON video_outputs(product_id);
            CREATE INDEX IF NOT EXISTS idx_job_assets_job_id ON job_assets(job_id);
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
        }
        if "sound_required" not in columns:
            connection.execute("ALTER TABLE jobs ADD COLUMN sound_required INTEGER NOT NULL DEFAULT 1")
        product_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        if "video_style" not in product_columns:
            connection.execute("ALTER TABLE products ADD COLUMN video_style TEXT")
        if "duration_seconds" not in product_columns:
            connection.execute("ALTER TABLE products ADD COLUMN duration_seconds INTEGER")
        video_output_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(video_outputs)").fetchall()
        }
        if "token_consumption" not in video_output_columns:
            connection.execute("ALTER TABLE video_outputs ADD COLUMN token_consumption INTEGER")
        if "token_unit_price_per_million" not in video_output_columns:
            connection.execute("ALTER TABLE video_outputs ADD COLUMN token_unit_price_per_million REAL")
        if "estimated_price_usd" not in video_output_columns:
            connection.execute("ALTER TABLE video_outputs ADD COLUMN estimated_price_usd REAL")
