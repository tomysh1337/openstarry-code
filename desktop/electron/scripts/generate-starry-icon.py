"""Generate the OpenStarry Code desktop icon set from one raster master."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUTPUT_SIZE = 1024
SCALE = 2
WORK_SIZE = OUTPUT_SIZE * SCALE
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def scaled(value: float) -> int:
    return round(value * SCALE)


def rotate_point(
    point: tuple[float, float], center: tuple[float, float], angle_degrees: float
) -> tuple[float, float]:
    angle = math.radians(angle_degrees)
    x, y = point
    cx, cy = center
    return (
        cx + (x - cx) * math.cos(angle) - (y - cy) * math.sin(angle),
        cy + (x - cx) * math.sin(angle) + (y - cy) * math.cos(angle),
    )


def draw_background() -> Image.Image:
    image = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), (0, 0, 0, 0))
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    inset = scaled(44)
    mask_draw.rounded_rectangle(
        (inset, inset, WORK_SIZE - inset, WORK_SIZE - inset),
        radius=scaled(218),
        fill=255,
    )

    gradient = Image.new("RGBA", image.size)
    gradient_draw = ImageDraw.Draw(gradient)
    top = (7, 12, 28)
    bottom = (20, 28, 48)
    for y in range(WORK_SIZE):
        t = y / (WORK_SIZE - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom, strict=True))
        gradient_draw.line((0, y, WORK_SIZE, y), fill=(*color, 255))
    image.paste(gradient, (0, 0), mask)

    edge = Image.new("RGBA", image.size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge)
    edge_draw.rounded_rectangle(
        (inset, inset, WORK_SIZE - inset, WORK_SIZE - inset),
        radius=scaled(218),
        outline=(111, 224, 255, 210),
        width=scaled(8),
    )
    edge_draw.rounded_rectangle(
        (
            inset + scaled(17),
            inset + scaled(17),
            WORK_SIZE - inset - scaled(17),
            WORK_SIZE - inset - scaled(17),
        ),
        radius=scaled(201),
        outline=(255, 255, 255, 30),
        width=scaled(3),
    )
    image.alpha_composite(edge)
    return image


def draw_star_field(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    stars = (
        (184, 221, 5, (151, 231, 255, 210)),
        (269, 152, 3, (255, 255, 255, 190)),
        (381, 203, 4, (108, 181, 255, 190)),
        (590, 155, 3, (255, 255, 255, 200)),
        (737, 202, 5, (255, 177, 138, 210)),
        (829, 310, 3, (255, 255, 255, 180)),
        (169, 430, 3, (255, 255, 255, 180)),
        (844, 499, 5, (126, 222, 255, 200)),
        (189, 647, 5, (95, 179, 255, 190)),
        (817, 704, 3, (255, 255, 255, 175)),
        (705, 824, 5, (255, 162, 125, 190)),
        (525, 854, 3, (255, 255, 255, 190)),
        (329, 814, 4, (121, 218, 255, 190)),
        (224, 758, 3, (255, 255, 255, 170)),
    )
    for x, y, radius, color in stars:
        r = scaled(radius)
        cx, cy = scaled(x), scaled(y)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)

    for x, y, radius, color in (
        (238, 321, 17, (146, 230, 255, 225)),
        (775, 608, 14, (255, 174, 135, 225)),
    ):
        cx, cy = scaled(x), scaled(y)
        outer = scaled(radius)
        inner = scaled(max(2, radius * 0.22))
        draw.polygon(
            (
                (cx, cy - outer),
                (cx + inner, cy - inner),
                (cx + outer, cy),
                (cx + inner, cy + inner),
                (cx, cy + outer),
                (cx - inner, cy + inner),
                (cx - outer, cy),
                (cx - inner, cy - inner),
            ),
            fill=color,
        )


def draw_orbit(image: Image.Image) -> None:
    orbit = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(orbit)
    box = tuple(scaled(value) for value in (157, 304, 867, 720))
    draw.ellipse(box, outline=(70, 157, 227, 150), width=scaled(13))
    draw.arc(box, start=195, end=318, fill=(100, 225, 255, 255), width=scaled(18))
    draw.arc(box, start=18, end=75, fill=(255, 128, 94, 240), width=scaled(18))
    orbit = orbit.rotate(
        17, resample=Image.Resampling.BICUBIC, center=(WORK_SIZE // 2, WORK_SIZE // 2)
    )
    image.alpha_composite(orbit)

    center = (512.0, 512.0)
    particles = (
        (
            (512 + 355 * math.cos(math.radians(235)), 512 + 208 * math.sin(math.radians(235))),
            13,
            (143, 235, 255, 255),
        ),
        (
            (512 + 355 * math.cos(math.radians(37)), 512 + 208 * math.sin(math.radians(37))),
            11,
            (255, 142, 104, 255),
        ),
    )
    draw = ImageDraw.Draw(image)
    for point, radius, color in particles:
        x, y = rotate_point(point, center, 17)
        cx, cy, r = scaled(x), scaled(y), scaled(radius)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def star_points(center: tuple[int, int]) -> list[tuple[int, int]]:
    cx, cy = center
    radii = (240, 58, 132, 58, 240, 58, 132, 58) * 2
    points: list[tuple[int, int]] = []
    for index, radius in enumerate(radii):
        angle = math.radians(-90 + index * 22.5)
        points.append(
            (
                cx + scaled(radius) * math.cos(angle),
                cy + scaled(radius) * math.sin(angle),
            )
        )
    return [(round(x), round(y)) for x, y in points]


def draw_primary_star(image: Image.Image) -> None:
    center = (WORK_SIZE // 2, WORK_SIZE // 2)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).polygon(star_points(center), fill=255)

    glow = Image.new("RGBA", image.size, (86, 211, 255, 0))
    glow.putalpha(mask.filter(ImageFilter.GaussianBlur(scaled(28))))
    image.alpha_composite(glow)

    fill = Image.new("RGBA", image.size)
    fill_draw = ImageDraw.Draw(fill)
    top = (255, 255, 255)
    bottom = (74, 205, 255)
    for y in range(scaled(270), scaled(755)):
        t = (y - scaled(270)) / scaled(485)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom, strict=True))
        fill_draw.line((scaled(270), y, scaled(755), y), fill=(*color, 255))
    image.paste(fill, (0, 0), mask)

    outline = Image.new("RGBA", image.size, (0, 0, 0, 0))
    outline_draw = ImageDraw.Draw(outline)
    outline_draw.line(
        star_points(center) + [star_points(center)[0]],
        fill=(220, 250, 255, 245),
        width=scaled(5),
        joint="curve",
    )
    image.alpha_composite(outline)

    core = scaled(31)
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (center[0] - core, center[1] - core, center[0] + core, center[1] + core),
        fill=(8, 20, 42, 255),
        outline=(255, 255, 255, 230),
        width=scaled(5),
    )


def build_master() -> Image.Image:
    image = draw_background()
    draw_star_field(image)
    draw_orbit(image)
    draw_primary_star(image)
    return image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    icon = build_master()
    icon.save(ASSETS_DIR / "icon.png", format="PNG", optimize=True)
    icon.save(
        ASSETS_DIR / "icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    icon.save(
        ASSETS_DIR / "icon.icns",
        format="ICNS",
        sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)],
    )


if __name__ == "__main__":
    main()
