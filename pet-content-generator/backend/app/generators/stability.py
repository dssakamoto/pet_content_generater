import asyncio
import uuid
from pathlib import Path

import httpx

from app.generators.base import ImageGenerator
from app.config import settings


class StabilityImageGenerator(ImageGenerator):
    _API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

    def __init__(self):
        if not settings.stability_api_key:
            raise ValueError("STABILITY_API_KEY is not configured in .env")
        self._api_key = settings.stability_api_key

    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        animal_label = "cat" if animal == "cat" else "dog"
        prompt = (
            f"A cute and adorable {animal_label}, theme: {theme}, "
            "soft pastel colors, heartwarming, high quality photograph"
        )

        async def _generate_one() -> Path:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self._API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Accept": "image/*",
                    },
                    data={
                        "prompt": prompt,
                        "aspect_ratio": "1:1",
                        "output_format": "png",
                    },
                )
                response.raise_for_status()
            out_path = settings.output_dir / f"{uuid.uuid4()}.png"
            out_path.write_bytes(response.content)
            return out_path

        return list(await asyncio.gather(*[_generate_one() for _ in range(count)]))
