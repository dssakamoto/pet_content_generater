import asyncio
import uuid
from pathlib import Path

from app.generators.base import ImageGenerator
from app.config import settings

# Imagen 3 (imagen-3.0-generate-002) は Vertex AI 専用のため使用不可。
# 代わりに Gemini 2.0 Flash の画像生成モードを使用する。
MODEL = "gemini-2.0-flash-exp-image-generation"


class GeminiImageGenerator(ImageGenerator):
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        from google import genai
        self._client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        from google.genai import types

        animal_label = "cat" if animal == "cat" else "dog"
        prompt = (
            f"Generate an image of a cute and adorable {animal_label}, "
            f"theme: {theme}, soft pastel colors, heartwarming, high quality photograph"
        )

        def _generate_one() -> Path:
            response = self._client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    mime = part.inline_data.mime_type or "image/png"
                    ext = "jpg" if "jpeg" in mime else "png"
                    out_path = settings.output_dir / f"{uuid.uuid4()}.{ext}"
                    out_path.write_bytes(part.inline_data.data)
                    return out_path
            raise ValueError("Gemini response contained no image data")

        loop = asyncio.get_running_loop()
        results = await asyncio.gather(
            *[loop.run_in_executor(None, _generate_one) for _ in range(count)]
        )
        return list(results)
