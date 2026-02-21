import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.generators.base import ImageGenerator
from app.generators.mock import MockImageGenerator
from app.video.composer import VideoComposer

router = APIRouter()
composer = VideoComposer()


def _build_generator() -> ImageGenerator:
    name = settings.image_generator.lower()
    if name == "gemini":
        from app.generators.gemini import GeminiImageGenerator
        return GeminiImageGenerator()
    if name == "openai":
        from app.generators.openai_gen import OpenAIImageGenerator
        return OpenAIImageGenerator()
    if name == "stability":
        from app.generators.stability import StabilityImageGenerator
        return StabilityImageGenerator()
    return MockImageGenerator()


generator = _build_generator()


class ImageRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    animal: str = Field(default="cat", pattern="^(cat|dog|random)$")
    count: int = Field(default=4, ge=1, le=8)


class VideoRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=200)
    animal: str = Field(default="cat", pattern="^(cat|dog|random)$")


@router.post("/generate/image")
async def generate_image(req: ImageRequest):
    animal = req.animal
    if animal == "random":
        animal = random.choice(["cat", "dog"])

    try:
        paths = await generator.generate(req.theme, animal, req.count)
        urls = [f"/outputs/{p.name}" for p in paths]
        return {"images": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/video")
async def generate_video(req: VideoRequest):
    animal = req.animal
    if animal == "random":
        animal = random.choice(["cat", "dog"])

    try:
        paths = await generator.generate(req.theme, animal, 4)
        video_path = await composer.compose(paths, req.theme)
        return {"video": f"/outputs/{video_path.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
