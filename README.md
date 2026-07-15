# Ecommerce Video Generator

Turns a product spreadsheet (SKU, description, reference images) into AI-generated
product videos. A FastAPI backend parses the workbook, builds a video-generation
prompt per product, submits it to a Seedance-compatible video model, and tracks
job/product status until the rendered videos are ready to download. A React
frontend drives the whole flow: upload, monitor, review, and retry.

## Architecture

```
React (Vite)  --->  FastAPI backend  --->  LLM provider (prompt generation)
                         |                 Seedance provider (video generation)
                         |                 BytePlus TOS (asset storage)
                         v
                    SQLite (job/product state)
                    Local filesystem (uploads, rendered videos, asset caches)
```

- `app/`: FastAPI backend and video-generation pipeline — the only server-side layer.
- `frontend/`: React + Vite single-page app — the only web UI.

## Repository Layout

```
app/
  main.py                 FastAPI app factory and API routes
  db.py                   SQLite schema and migrations
  repository.py           Persistence helpers (jobs, products, assets)
  schemas.py               Shared Pydantic models
  settings.py             Env-driven configuration (reads .env only)
  services/
    excel_parser.py       Workbook -> ProductRow parsing
    prompt_builder.py     Product data -> video-generation prompt
    job_runner.py         Async job/product orchestration and concurrency control
    providers.py          LLM + Seedance provider clients (live/mock)
    asset_library.py      Ark reusable asset group/upload handling
frontend/
  src/pages/              Route-level pages (create job, monitor, results)
  src/components/         Shared UI components
  src/store/              Zustand client state
  src/lib/                API client and shared types
data/                     Runtime SQLite DB, uploads, rendered videos, asset caches (gitignored)
ecommerceskills.md         Prompt-writing rules consumed by the prompt builder
main.py                   Root launcher for the backend (uvicorn)
requirements.txt          Backend dependencies
```

## Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Credentials for the LLM provider, Seedance provider, and BytePlus TOS (or run in `mock` mode without them)

## Setup

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in the values described in Configuration below
python3 main.py
```

Backend runs at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend runs at `http://127.0.0.1:5173` and proxies API requests to the FastAPI backend.

## Configuration

**These credentials are set only through `.env`, read once at process
startup.** There is no in-app way to view or change them — edit `.env` and
restart the backend for changes to take effect.

| Variable | Purpose |
|---|---|
| `ARK_API_KEY` | Auth for both the LLM (prompt generation) and Seedance (video generation) providers. |
| `ARK_PROJECT` | Ark project name. |
| `ARK_MODEL_ENDPOINT` | Ark model endpoint used for video generation. |
| `BYTEPLUS_AK`, `BYTEPLUS_SK` | BytePlus access key / secret key. |
| `TOS_REGION`, `TOS_BUCKET_NAME` | BytePlus TOS object storage location for reference/generated assets. |

These are the only environment variables this app actually reads for provider
setup — [`.env.example`](.env.example) mirrors this list. Everything else
`app/settings.py` supports (LLM/Seedance mode overrides, job/upload limits,
data paths, host/port) has a working default and doesn't need to be set.

## API Overview

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/jobs` | Upload a workbook + config, create a job |
| `GET` | `/api/jobs/{job_id}` | Job status and counts |
| `GET` | `/api/jobs/{job_id}/products` | Per-product status |
| `POST` | `/api/jobs/{job_id}/retry` | Retry failed products |
| `POST` | `/api/jobs/{job_id}/products/{product_id}/regenerate` | Regenerate one product with a custom prompt |
| `GET` | `/api/jobs/{job_id}/download/{product_id}` | Download a rendered video |

## Testing

```bash
pip install pytest
pytest
```

> No `tests/` directory is currently checked in — `.pytest_cache` shows a prior
> test suite covering the excel parser, prompt builder, job API, and Seedance
> payload building. Restore or rewrite these before relying on `pytest` in CI.

## Data & Storage

`data/` holds the SQLite job database, uploaded workbooks, rendered videos, and
Ark asset caches. It is runtime state, not source, and is gitignored — back it
up separately if it needs to persist across deployments.

## Security Notes

- Real credentials belong in `.env` only; `.env.example` documents the required
  keys with empty values. `.env` is gitignored — never commit it.
- `venv/`, `frontend/node_modules/`, `frontend/dist/`, and `.tools/` are local
  build/runtime artifacts and are excluded from version control — reinstall
  them with the setup commands above rather than committing them.

## Notes

- `ecommerceskills.md` is mandatory for prompt generation and is used by the prompt builder.
- The workbook is the only required user upload in the current flow.
- Job history is stored in `data/app.db`.
