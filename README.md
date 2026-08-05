# Ecommerce Video Generator

Turns a product spreadsheet (SKU, description, reference images, per-row video style) into AI-generated product videos via BytePlus Seedance 2.0. A FastAPI backend parses the workbook, builds a style-specific prompt per product, submits it to Seedance, and tracks job state in SQLite. A React frontend drives upload, monitoring, review, and retry.

## Architecture

```
React (Vite)  --->  FastAPI backend  --->  BytePlus Ark LLM (prompt generation)
                         |                 BytePlus Seedance 2.0 (video generation)
                         |                 BytePlus TOS (asset storage)
                         v
                    SQLite (job/product state)
```

Credentials are passed per-request via headers (API gate) — the backend never persists API keys. Users enter their Ark API key + BytePlus AK/SK in the browser; the frontend stores them in `sessionStorage` and attaches them as headers on every API call.

## Repository Layout

```
app/                        FastAPI backend
  main.py                   App factory + API routes
  db.py                     SQLite schema + migrations
  repository.py             Persistence helpers
  schemas.py                Pydantic models
  settings.py               Env-driven configuration
  services/
    excel_parser.py         Workbook parsing + embedded image extraction
    prompt_builder.py       Deterministic style-specific prompt builders
    providers.py            LLM + Seedance provider adapters (live only)
    job_runner.py           Async job orchestrator (FSM + concurrency)
    asset_library.py        TOS upload + Ark asset registration
frontend/                   React + Vite + Tailwind + Zustand SPA
  src/pages/                Credentials, CreateJob, JobMonitor, Results
  src/components/           Shared UI components
  src/store/                Zustand state
  src/lib/                  API client + types
deploy/                     Docker deployment
  Dockerfile.backend        Python 3.12-slim backend image
  Dockerfile.frontend       Multi-stage Node → nginx frontend image
  docker-compose.yml        Backend + frontend + named volume
  nginx.conf                SPA fallback + /api reverse proxy
Doc/                        Reference docs
  ecommerceskills.md        Prompt-writing style guide (loaded by prompt_builder)
  UGC_videos.md             UGC skill system prompt (loaded by providers)
  Seedance-2.0 Audio Guidelines.md  Audio policy reference
  Vg_spec.md                BytePlus Video Generation API spec
main.py                     Root launcher (uvicorn)
requirements.txt           Backend dependencies
```

## Video Styles

Each workbook row specifies a video style. The backend routes to a dedicated prompt builder per style:

| Style | Builder | Description |
|---|---|---|
| `UGC` | `_build_ugc_prompt` | Handheld selfie, mandatory spoken audio, LLM-authored dialogue |
| `UGC Skill` | LLM-authored via `UGC_videos.md` | Fully LLM-authored sectioned prompt, fixed camera, named performer |
| `Cinematic` | `_build_cinematic_prompt` | Hero shot, slow push-in, no people |
| `CGI Showcase` | `_build_cgi_showcase_prompt` | Photoreal CG, abstract void, weightless motion-control |
| `Review` | `_build_review_prompt` | Single-take handheld phone review, lip-synced dialogue |
| `Hook` | `_build_hook_prompt` | Opening beat only, 4 hook archetypes |
| `Lifestyle Scenes` | `_build_lifestyle_scenes_prompt` | Same product across 3 environments |
| `Presenter` | `_build_presenter_prompt` | Talking-head, locked-off camera, verbatim script |
| *other* | Generic fallback | Standard hook → mid → closing structure |

All prompts are sanitized against the Seedance-2.0 Audio Guidelines before submit.

## Local Development

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Backend runs at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173` and proxies `/api` to the backend.

## Deployment

### Docker

```bash
docker compose -f deploy/docker-compose.yml up -d
```

Or build and push manually:

```bash
docker buildx build --platform linux/amd64 -f deploy/Dockerfile.backend -t <user>/evg-backend:latest --push .
docker buildx build --platform linux/amd64 -f deploy/Dockerfile.frontend -t <user>/evg-frontend:latest --push .
```

### Environment

The `.env` file on the server only needs:

| Variable | Default | Purpose |
|---|---|---|
| `SEEDANCE_MODE` | `live` | `live` or `prompt_only` (dry-run, no API calls) |
| `ARK_PROJECT` | `default` | Ark project name |
| `TOS_REGION` | — | BytePlus TOS region |
| `TOS_BUCKET_NAME` | — | BytePlus TOS bucket |

`ARK_API_KEY`, `BYTEPLUS_AK`, and `BYTEPLUS_SK` are **not** in `.env` — users provide them per-request via the browser.
