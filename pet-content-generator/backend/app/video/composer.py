import asyncio
import shutil
import uuid
from pathlib import Path

from app.config import settings


class VideoComposer:
    """Compose multiple images into a vertical short video (1080x1920) using ffmpeg."""

    async def compose(
        self,
        image_paths: list[Path],
        theme: str,
        duration_per_image: float = 3.75,
        output_width: int = 1080,
        output_height: int = 1920,
    ) -> Path:
        """Compose images into a vertical video with zoom and fade effects.

        Each image is displayed for `duration_per_image` seconds with a slow
        zoom effect and crossfade transitions, producing ~15s of video.
        """
        if not image_paths:
            raise ValueError("No images provided")

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found")

        output_dir = settings.output_dir
        output_file = output_dir / f"{uuid.uuid4().hex}.mp4"
        total_images = len(image_paths)
        fade_duration = 0.5
        fps = 25
        frames_per_image = int(duration_per_image * fps)

        # Build ffmpeg command
        cmd: list[str] = [ffmpeg_path, "-y"]

        # Add inputs
        for img_path in image_paths:
            cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img_path)])

        # Build filter_complex
        filter_parts: list[str] = []
        for i in range(total_images):
            zoom_start = 1.0
            zoom_end = 1.15
            filter_parts.append(
                f"[{i}:v]"
                f"scale={output_width * 2}:{output_height * 2}:force_original_aspect_ratio=increase,"
                f"crop={output_width * 2}:{output_height * 2},"
                f"zoompan=z='min({zoom_start}+on*{(zoom_end - zoom_start) / frames_per_image},{zoom_end})'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames_per_image}:s={output_width}x{output_height}:fps={fps},"
                f"setsar=1,"
                f"fade=t=in:st=0:d={fade_duration},"
                f"fade=t=out:st={duration_per_image - fade_duration}:d={fade_duration}"
                f"[v{i}]"
            )

        concat_inputs = "".join(f"[v{i}]" for i in range(total_images))
        filter_parts.append(f"{concat_inputs}concat=n={total_images}:v=1:a=0[outv]")

        filter_complex = ";".join(filter_parts)

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-movflags", "faststart",
            "-t", str(duration_per_image * total_images),
            str(output_file),
        ])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

        return output_file
