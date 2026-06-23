# BanglaRAG frontend (web/)

The user interface — login, chat, and corpus admin — built with **Vite + React +
TypeScript + Tailwind CSS + shadcn/ui**.

## How it fits the deployment

`vite build` outputs the bundle into **`../frontend`** (relative asset paths via
`base: "./"`). That is the directory every deploy target already serves:

- **FastAPI / HF Space** — `app/main.py` mounts `frontend/` as a static SPA.
- **GitHub Pages** — the workflow publishes the `frontend/` directory.

So the built output is committed to `frontend/`; there is no separate build step in
the Docker image or CI. After changing anything under `web/src`, rebuild and commit
the regenerated `frontend/`.

## Commands

```bash
cd web
npm install        # once
npm run dev        # local dev server (expects the API at /api or BANGLARAG_API_BASE)
npm run build      # rebuild ../frontend (commit the result)
```

## API base resolution (src/lib/api.ts)

1. `window.BANGLARAG_API_BASE` if defined, else
2. `localStorage["banglaragApiBase"]`, else
3. the hosted Space API when served from `*.github.io`, else
4. same-origin `/api`.
