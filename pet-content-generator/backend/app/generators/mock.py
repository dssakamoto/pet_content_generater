import math
import random
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.generators.base import ImageGenerator

# Pastel color palettes per mood
PALETTES = {
    "default": [
        ((255, 218, 233), (255, 154, 192)),  # pink
        ((200, 230, 255), (130, 190, 255)),  # blue
        ((210, 255, 210), (140, 230, 140)),  # green
        ((255, 245, 200), (255, 220, 130)),  # yellow
        ((230, 210, 255), (180, 150, 255)),  # purple
        ((255, 225, 200), (255, 180, 130)),  # orange
    ],
}

# Simple silhouette drawing functions
CAT_SILHOUETTE_COLOR = (255, 255, 255, 80)
DOG_SILHOUETTE_COLOR = (255, 255, 255, 80)


def _draw_cat_silhouette(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    """Draw a simple cat face silhouette."""
    color = CAT_SILHOUETTE_COLOR
    r = size // 2

    # Head circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Left ear
    ear_size = r // 2
    draw.polygon(
        [
            (cx - r + ear_size // 2, cy - r + ear_size // 4),
            (cx - r - ear_size // 3, cy - r - ear_size),
            (cx - r + ear_size, cy - r - ear_size // 3),
        ],
        fill=color,
    )
    # Right ear
    draw.polygon(
        [
            (cx + r - ear_size // 2, cy - r + ear_size // 4),
            (cx + r + ear_size // 3, cy - r - ear_size),
            (cx + r - ear_size, cy - r - ear_size // 3),
        ],
        fill=color,
    )

    # Eyes
    eye_r = r // 6
    draw.ellipse(
        [cx - r // 3 - eye_r, cy - eye_r, cx - r // 3 + eye_r, cy + eye_r],
        fill=(100, 100, 100, 120),
    )
    draw.ellipse(
        [cx + r // 3 - eye_r, cy - eye_r, cx + r // 3 + eye_r, cy + eye_r],
        fill=(100, 100, 100, 120),
    )

    # Nose
    nose_r = r // 10
    draw.ellipse(
        [cx - nose_r, cy + r // 6 - nose_r, cx + nose_r, cy + r // 6 + nose_r],
        fill=(255, 180, 180, 150),
    )

    # Whiskers
    whisker_color = (200, 200, 200, 100)
    for dy in [-r // 8, 0, r // 8]:
        draw.line([(cx - r // 3, cy + r // 4 + dy), (cx - r, cy + r // 4 + dy - r // 10)], fill=whisker_color, width=2)
        draw.line([(cx + r // 3, cy + r // 4 + dy), (cx + r, cy + r // 4 + dy - r // 10)], fill=whisker_color, width=2)


def _draw_dog_silhouette(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    """Draw a simple dog face silhouette."""
    color = DOG_SILHOUETTE_COLOR
    r = size // 2

    # Head circle (slightly wider)
    draw.ellipse([cx - r, cy - r + r // 6, cx + r, cy + r], fill=color)

    # Floppy ears
    ear_w = r // 2
    ear_h = r
    draw.ellipse(
        [cx - r - ear_w // 2, cy - r // 4, cx - r + ear_w, cy - r // 4 + ear_h],
        fill=color,
    )
    draw.ellipse(
        [cx + r - ear_w, cy - r // 4, cx + r + ear_w // 2, cy - r // 4 + ear_h],
        fill=color,
    )

    # Eyes
    eye_r = r // 6
    draw.ellipse(
        [cx - r // 3 - eye_r, cy - eye_r, cx - r // 3 + eye_r, cy + eye_r],
        fill=(80, 60, 40, 140),
    )
    draw.ellipse(
        [cx + r // 3 - eye_r, cy - eye_r, cx + r // 3 + eye_r, cy + eye_r],
        fill=(80, 60, 40, 140),
    )

    # Nose
    nose_r = r // 5
    draw.ellipse(
        [cx - nose_r, cy + r // 4 - nose_r, cx + nose_r, cy + r // 4 + nose_r],
        fill=(60, 40, 30, 180),
    )

    # Mouth
    draw.arc(
        [cx - r // 4, cy + r // 6, cx + r // 4, cy + r // 2],
        start=0,
        end=180,
        fill=(100, 80, 60, 120),
        width=2,
    )


def _create_gradient(width: int, height: int, color_top: tuple, color_bottom: tuple) -> Image.Image:
    """Create a vertical gradient image."""
    # Build one column as a gradient, then stretch to full width
    base = Image.new("RGBA", (1, height))
    for y in range(height):
        ratio = y / height
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        base.putpixel((0, y), (r, g, b, 255))
    return base.resize((width, height), Image.NEAREST)


def _draw_decorations(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    """Draw random soft decorative circles for a dreamy feel."""
    for _ in range(random.randint(5, 12)):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(10, 60)
        alpha = random.randint(20, 60)
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=(255, 255, 255, alpha),
        )


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to find a font that supports Japanese characters."""
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


class MockImageGenerator(ImageGenerator):
    async def generate(self, theme: str, animal: str, count: int = 4) -> list[Path]:
        output_dir = settings.output_dir
        paths: list[Path] = []
        palette_list = PALETTES["default"]

        for i in range(count):
            width, height = 1080, 1080
            colors = random.choice(palette_list)
            img = _create_gradient(width, height, colors[0], colors[1])
            draw = ImageDraw.Draw(img, "RGBA")

            # Decorative elements
            _draw_decorations(draw, width, height)

            # Animal silhouette
            silhouette_size = random.randint(200, 350)
            sx = random.randint(silhouette_size, width - silhouette_size)
            sy = random.randint(height // 3, height - silhouette_size)
            if animal == "cat":
                _draw_cat_silhouette(draw, sx, sy, silhouette_size)
            else:
                _draw_dog_silhouette(draw, sx, sy, silhouette_size)

            # Theme text overlay
            font = _find_font(48)
            label = f"{theme}"
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            tx = (width - tw) // 2
            ty = 80

            # Text shadow
            draw.text((tx + 2, ty + 2), label, fill=(0, 0, 0, 60), font=font)
            draw.text((tx, ty), label, fill=(255, 255, 255, 220), font=font)

            # Animal label
            animal_label = "🐱" if animal == "cat" else "🐶"
            small_font = _find_font(36)
            draw.text((width - 100, height - 80), animal_label, fill=(255, 255, 255, 200), font=small_font)

            # Convert to RGB for PNG save
            final = Image.new("RGB", (width, height), (255, 255, 255))
            final.paste(img, mask=img.split()[3])

            filename = f"{uuid.uuid4().hex}.png"
            filepath = output_dir / filename
            final.save(filepath, "PNG")
            paths.append(filepath)

        return paths
