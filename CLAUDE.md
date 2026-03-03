# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

This is a Docker Compose project. Docker Desktop must be running.

```bash
# Start everything (builds images on first run)
cd pet-content-generator
docker compose up --build

# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

Source code hot-reloads via bind mounts for both backend (`backend/app/`) and frontend (`frontend/src/`, `frontend/index.html`).

There are no tests, linters, or CI pipelines configured.

## Architecture

**pet-content-generator/** — Fullstack MVP that generates pet-themed images and short vertical videos from a text theme input. Japanese UI text.

### Backend (FastAPI, Python 3.11)
- `app/main.py` — FastAPI app, CORS, mounts `/outputs` static files and `/api` router
- `app/routers/generate.py` — Two endpoints: `POST /api/generate/image` and `POST /api/generate/video`
- `app/generators/base.py` — `ImageGenerator` ABC (Strategy pattern)
- `app/generators/mock.py` — `MockImageGenerator`: creates 1080x1080 images with Pillow (pastel gradients, animal silhouettes, theme text overlay)
- `app/generators/gemini.py` — `GeminiImageGenerator`: uses `gemini-2.0-flash-exp-image-generation` via `generateContent` + `response_modalities=["IMAGE","TEXT"]`. Runs sync SDK in `run_in_executor`; count requests fired concurrently with `asyncio.gather`
- `app/generators/openai_gen.py` — `OpenAIImageGenerator`: uses DALL-E 3 (`n=1` per request); count images generated concurrently with `asyncio.gather`
- `app/generators/stability.py` — `StabilityImageGenerator`: calls Stability AI v2beta REST API (`/stable-image/generate/core`) via `httpx`; count requests fired concurrently
- `app/routers/generate.py` — `_build_generator()` factory selects implementation based on `IMAGE_GENERATOR` env var at startup
- `app/video/composer.py` — `VideoComposer`: stitches images into a 1080x1920 vertical video via ffmpeg subprocess (`asyncio.create_subprocess_exec`, not ffmpeg-python lib)
- `app/publishers/base.py` — `Publisher` ABC + `PublishResult`/`ContentMetadata` dataclasses (no implementations yet)
- `app/config.py` — `Settings` via pydantic-settings, reads `.env`. Optional API keys: `gemini_api_key`, `openai_api_key`, `stability_api_key` (all `str | None = None`)

### Frontend (React 18, Vite, TypeScript, Tailwind CSS)
- `src/App.tsx` — Container component managing all state; `handleGenerate` stabilized with `useCallback([theme, animal, format])`; derived values (`label`, `isDisabled`) computed during render
- `src/components/ThemeInput.tsx` — Uncontrolled-style input; re-renders on every keypress (correct behavior)
- `src/components/OutputSelector.tsx` — Wrapped with `memo()`; skips re-render while user is typing in theme field
- `src/components/GenerateButton.tsx` — Wrapped with `memo()`; only re-renders when `loading`/`disabled`/`label` change
- `src/components/Preview.tsx` — Wrapped with `memo()`; only re-renders when `result` changes
- `src/api/client.ts` — `generateImage()` and `generateVideo()` fetch wrappers
- `src/types/index.ts` — Shared TypeScript interfaces
- `vite.config.ts` — Proxies `/api` and `/outputs` to `http://backend:8000` (container networking)
- `src/index.css` — CSS custom properties (`--accent`, `--ink`, `--bg` etc.), Google Fonts import (Playfair Display + Outfit), `.polaroid` and `.stamp-btn` component classes

### Key Design Decisions
- **ffmpeg via subprocess**, not ffmpeg-python — complex `filter_complex` graphs (zoompan + fade + concat) are more reliable with raw command construction
- **Pillow gradient optimization** — 1px-wide column resized with `Image.NEAREST` instead of per-pixel loops
- **Noto CJK fonts** installed in backend Dockerfile for Japanese text rendering; font fallback chain in `mock.py:_find_font()`
- **Docker named volume** (`backend-outputs`) persists generated files across container restarts; source code uses bind mounts for hot-reload
- **Frontend design system** — CSS custom properties defined in `index.css` (not Tailwind config) for color tokens; component-specific classes (`.polaroid`, `.stamp-btn`) also in `index.css`; inline styles used for dynamic/state-driven values in TSX components
- **React re-render optimization** — `OutputSelector`, `GenerateButton`, `Preview` wrapped with `memo()`; `handleGenerate` stabilized with `useCallback`; `useState` setters (`setAnimal` etc.) passed directly as props (already stable references); conditional rendering uses ternary `? : null` not `&&` (per `rendering-conditional-render` rule)
- **API keys are all optional** — `Settings` fields default to `None`; backend starts without any key set. Implementations should guard with `if not settings.gemini_api_key: raise ...`

### Extension Points
- New image generator: implement `ImageGenerator` ABC, switch via `IMAGE_GENERATOR` env var
- Gemini video generation: use `settings.gemini_api_key` in a new `video/` implementation; swap out `VideoComposer` or add a new endpoint
- SNS publishing: implement `Publisher` ABC, add router endpoint
- New animal types: add silhouette drawing function in `mock.py`, update Pydantic regex in `generate.py`

### Environment Variables

`.env` (gitignored) and `.env.example` (committed) live at `pet-content-generator/`.

| Variable | Default | Purpose |
|---|---|---|
| `IMAGE_GENERATOR` | `mock` | `mock` \| `gemini` \| `openai` \| `stability` |
| `OUTPUT_DIR` | `/app/app/outputs` | Output path inside container |
| `GEMINI_API_KEY` | — | Google Gemini API（無料キーで使用可） |
| `OPENAI_API_KEY` | — | OpenAI / DALL-E 3 |
| `STABILITY_API_KEY` | — | Stability AI v2beta |

**Gemini モデルについて:**
- 使用モデル: `gemini-2.0-flash-exp-image-generation`（`generateContent` API）
- `imagen-3.0-generate-002` / `imagen-4.0-*` は `predict` API を使う Vertex AI 専用モデルのため、通常の Gemini API キーでは使用不可
- 利用可能モデルの確認: `client.models.list()` で `supported_actions` を確認する

## API Contracts

```
POST /api/generate/image
  Body: { "theme": str, "animal": "cat"|"dog"|"random", "count": 1-8 }
  Response: { "images": ["/outputs/{uuid}.png", ...] }

POST /api/generate/video
  Body: { "theme": str, "animal": "cat"|"dog"|"random" }
  Response: { "video": "/outputs/{uuid}.mp4" }
```

## Other Directories

- `.agents/skills/` — Agent skill definitions installed via `npx skills add` (reference documentation, not runtime code). Works with Codex, Cursor, Gemini CLI. Not loaded by Claude Code (Claude Code uses `~/.claude/plugins/` instead).
