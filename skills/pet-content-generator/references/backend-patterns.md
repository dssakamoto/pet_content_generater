# Backend Patterns Reference

## Table of Contents
- [Project Structure](#project-structure)
- [FastAPI Entry Point](#fastapi-entry-point)
- [Configuration (pydantic-settings)](#configuration)
- [Generator Strategy Pattern](#generator-strategy-pattern)
- [Mock Image Generator (Pillow)](#mock-image-generator)
- [Video Composer (ffmpeg subprocess)](#video-composer)
- [Publisher Strategy Pattern (Future Extension)](#publisher-strategy-pattern)
- [Router / API Endpoints](#router--api-endpoints)
- [Dockerfile](#dockerfile)

## Project Structure

```
backend/
├── Dockerfile
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── routers/
    │   ├── __init__.py
    │   └── generate.py
    ├── generators/
    │   ├── __init__.py
    │   ├── base.py          # ABC
    │   └── mock.py          # Pillow implementation
    ├── video/
    │   ├── __init__.py
    │   └── composer.py      # ffmpeg subprocess
    ├── publishers/
    │   ├── __init__.py
    │   └── base.py          # ABC stub
    └── outputs/
        └── .gitkeep
```

## FastAPI Entry Point

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Pet Content Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")
```

Key points:
- CORS allows Vite dev server origin only
- Static files mounted at `/outputs` for generated content serving
- Router prefix `/api` groups all generation endpoints

## Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    image_generator: str = "mock"
    output_dir: Path = Path("/app/app/outputs")
    model_config = {"env_file": ".env"}

settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
```

- Uses `pydantic-settings` for env var / .env file loading
- `IMAGE_GENERATOR` env var selects the strategy (mock/dalle/stability)
- Output directory auto-created on import

## Generator Strategy Pattern

Abstract base class:

```python
from abc import ABC, abstractmethod

class ImageGenerator(ABC):
    @abstractmethod
    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        ...
```

Contract: accepts theme/animal/count, returns list of saved file paths. All generators must implement this async interface.

To add a new generator (e.g. DALL-E):
1. Create `generators/dalle.py` implementing `ImageGenerator`
2. Switch instantiation in router based on `settings.image_generator`

## Mock Image Generator

Pillow-based procedural image generation (1080x1080 PNG):

1. **Gradient background** - 1-pixel-wide column scaled to full width (performance optimized)
2. **Decorative circles** - 5-12 random semi-transparent white circles for dreamy effect
3. **Animal silhouette** - Programmatic cat face (pointed ears, whiskers) or dog face (floppy ears, nose)
4. **Theme text overlay** - Japanese text with shadow, centered top, using Noto CJK font
5. **Animal emoji label** - Bottom-right corner

Silhouette colors use `(255, 255, 255, 80)` RGBA for subtle overlay effect.

Font fallback chain for Japanese:
```python
font_paths = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
```

Pastel palette (6 gradient pairs):
- Pink, Blue, Green, Yellow, Purple, Orange

## Video Composer

Uses ffmpeg via `asyncio.create_subprocess_exec` (not ffmpeg-python lib) for reliable `filter_complex` handling.

Output: 1080x1920 vertical MP4 (YouTube Shorts format), ~15 seconds.

Per-image filter chain:
```
scale (2x) → crop → zoompan (1.0x→1.15x) → setsar → fade in/out
```

Then all clips concatenated:
```
[v0][v1]...[vN]concat=n=N:v=1:a=0[outv]
```

Settings: 25fps, libx264, yuv420p, movflags=faststart, 0.5s fade duration, 3.75s per image.

Important: Use subprocess directly instead of ffmpeg-python for complex filter_complex strings. The ffmpeg-python library struggles with multi-input filter graphs.

## Publisher Strategy Pattern

Future extension stub:

```python
@dataclass
class PublishResult:
    success: bool
    url: str | None = None
    message: str = ""

@dataclass
class ContentMetadata:
    title: str
    description: str = ""
    tags: list[str] | None = None

class Publisher(ABC):
    @abstractmethod
    async def publish(self, content_path: Path, metadata: ContentMetadata) -> PublishResult:
        ...
```

Extend by creating `publishers/twitter.py`, `publishers/youtube.py`, etc.

## Router / API Endpoints

```python
class ImageRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    animal: str = Field(default="cat", pattern="^(cat|dog|random)$")
    count: int = Field(default=4, ge=1, le=8)

class VideoRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    animal: str = Field(default="cat", pattern="^(cat|dog|random)$")
```

- `POST /api/generate/image` → `{ "images": ["/outputs/xxx.png", ...] }`
- `POST /api/generate/video` → `{ "video": "/outputs/xxx.mp4" }`
- "random" animal resolved server-side via `random.choice(["cat", "dog"])`

## Dockerfile

```dockerfile
FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg fonts-noto-cjk && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Critical system deps: `ffmpeg` (video), `fonts-noto-cjk` (Japanese text in Pillow).

## Requirements

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic-settings==2.7.1
Pillow==11.1.0
python-multipart==0.0.20
```
