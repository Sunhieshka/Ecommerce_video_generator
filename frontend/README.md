# Frontend

This directory contains the React + Vite frontend for the Ecommerce Video Generator.

## Responsibilities

- Upload the Excel workbook
- Configure output resolution and aspect ratio
- Monitor batch progress
- Review/edit prompts for individual products
- Preview generated videos and per-row usage/cost

## Development

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The Vite dev server runs on `http://127.0.0.1:5173`.

## Backend Integration

- API requests are proxied to the FastAPI backend on `http://127.0.0.1:8000`
- The frontend expects the backend APIs under `/api/*`

## Structure

- `src/pages/`: route-level screens
- `src/components/`: reusable UI components
- `src/lib/`: API client, shared frontend types, helpers
- `src/store/`: client-side state
