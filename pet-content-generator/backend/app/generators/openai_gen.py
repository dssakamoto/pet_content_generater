import asyncio
import base64
import uuid
from pathlib import Path

from app.generators.base import ImageGenerator
from app.config import settings


class OpenAIImageGenerator(ImageGenerator):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured in .env")

        import openai
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        animal_label = "cat" if animal == "cat" else "dog"
        prompt = (
            f"A cute and adorable {animal_label}, theme: {theme}, "
            "soft pastel colors, heartwarming, high quality photograph"
        )

        async def _generate_one() -> Path:
            # DALL-E 3 は n=1 のみ対応のため、count 分ループ
            response = await self._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                response_format="b64_json",
                n=1,
            )
            out_path = settings.output_dir / f"{uuid.uuid4()}.png"
            out_path.write_bytes(base64.b64decode(response.data[0].b64_json))
            return out_path

        return list(await asyncio.gather(*[_generate_one() for _ in range(count)]))
