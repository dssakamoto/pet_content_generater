from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


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
        """Publish content to a platform.

        Args:
            content_path: Path to the content file (image or video).
            metadata: Metadata for the post (title, description, tags).

        Returns:
            PublishResult with success status and optional URL.
        """
        ...
