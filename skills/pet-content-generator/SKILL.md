---
name: pet-content-generator
description: Generate a fullstack MVP that creates cute pet (cat/dog) images and YouTube Shorts vertical videos from a theme input. Uses FastAPI + Pillow + ffmpeg backend, React + Vite + TypeScript + TailwindCSS frontend, and Docker Compose for orchestration. Use when building content generation apps, media pipeline MVPs, or Docker-based fullstack projects with image/video generation capabilities. Also useful when implementing Strategy pattern for swappable generators/publishers, Pillow-based procedural image generation, or ffmpeg video composition from images.
---

# Pet Content Generator

Build a Docker-based fullstack MVP that generates pet-themed images and short vertical videos from a text theme input. The architecture uses Strategy pattern for future extensibility (swappable image generators, SNS publishers).

## Architecture

```
Frontend (React+Vite:5173)  →  Backend (FastAPI:8000)
  - Theme input                 - POST /api/generate/image
  - Animal selection             - POST /api/generate/video
  - Format toggle               - GET /outputs/{file}
  - Preview + Download          - generators/ (Strategy)
                                - video/ (ffmpeg)
                                - publishers/ (future)
```

Vite proxies `/api` and `/outputs` to the backend container. No direct browser-to-backend calls needed.

## Quick Start

1. Create project structure per the file layout in backend and frontend references
2. Write all backend files: main.py, config.py, router, generator ABC + mock, video composer, publisher ABC
3. Write all frontend files: App.tsx container, 4 presentational components, API client, types
4. Configure Docker Compose with hot-reload bind mounts
5. `docker compose up --build` and open `http://localhost:5173`

## Key Implementation Decisions

### Use subprocess for ffmpeg, not ffmpeg-python
The ffmpeg-python library struggles with complex multi-input `filter_complex` graphs. Use `asyncio.create_subprocess_exec` with manually constructed command args for reliable zoompan + fade + concat filters.

### Optimize Pillow gradients
Create a 1-pixel-wide gradient column and resize to full width with `Image.NEAREST` instead of per-pixel `putpixel` loops (orders of magnitude faster at 1080x1080).

### Install Noto CJK fonts in Dockerfile
Japanese theme text rendering requires `fonts-noto-cjk` package. Include font fallback chain in the image generator to handle varying install paths across distros.

### Named volume for outputs
Use a Docker named volume for `outputs/` to persist generated files across container restarts while keeping bind mounts for source code hot-reload.

## API Contracts

```
POST /api/generate/image
  Body: { "theme": str, "animal": "cat"|"dog"|"random", "count": 1-8 }
  Response: { "images": ["/outputs/{uuid}.png", ...] }

POST /api/generate/video
  Body: { "theme": str, "animal": "cat"|"dog"|"random" }
  Response: { "video": "/outputs/{uuid}.mp4" }
```

Pydantic validates all inputs. "random" animal resolved server-side.

## Extension Points

- **New image generator**: Implement `ImageGenerator` ABC in `generators/`, switch via `IMAGE_GENERATOR` env var
- **SNS publishing**: Implement `Publisher` ABC in `publishers/`, add router endpoint
- **New animal types**: Add to silhouette drawing functions and Pydantic regex pattern

## References

- **Backend patterns**: See [references/backend-patterns.md](references/backend-patterns.md) for FastAPI setup, Strategy pattern implementation, Pillow image generation, ffmpeg video composition, Dockerfile, and requirements
- **Frontend patterns**: See [references/frontend-patterns.md](references/frontend-patterns.md) for React component structure, state management, API client, Vite proxy config, TailwindCSS design system, and Dockerfile
- **Docker patterns**: See [references/docker-patterns.md](references/docker-patterns.md) for Docker Compose configuration, volume strategy, networking, and environment variables
