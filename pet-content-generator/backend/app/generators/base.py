from abc import ABC, abstractmethod
from pathlib import Path


class ImageGenerator(ABC):
    @abstractmethod
    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        """Generate images based on theme and animal type.

        Args:
            theme: The theme/mood for the images.
            animal: "cat" or "dog".
            count: Number of images to generate.

        Returns:
            List of file paths to the generated images.
        """
        ...
