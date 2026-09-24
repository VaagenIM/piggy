"""Font discovery and title fitting/wrapping."""

from pathlib import Path

import PIL.ImageDraw
import PIL.ImageFont

# This module lives in piggy/thumbnail_generator/, while static/ lives in piggy/.
_FONTS_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts" / "generator"

_FONT_PATHS = [
    # Reliable / general
    _FONTS_DIR / "Lato-Bold.ttf",
    _FONTS_DIR / "ArchivoBlack-Regular.ttf",
    _FONTS_DIR / "SpaceGrotesk-Bold.ttf",
    _FONTS_DIR / "Sora-ExtraBold.ttf",
    _FONTS_DIR / "LeagueSpartan-Bold.ttf",
    _FONTS_DIR / "Manrope-ExtraBold.ttf",
    _FONTS_DIR / "Montserrat-ExtraBold.ttf",
    _FONTS_DIR / "PlusJakartaSans-ExtraBold.ttf",
    _FONTS_DIR / "Outfit-ExtraBold.ttf",
    _FONTS_DIR / "Inter-Black.ttf",
    # Condensed / long-title friendly
    _FONTS_DIR / "BarlowCondensed-SemiBold.ttf",
    _FONTS_DIR / "Oswald-Bold.ttf",
    _FONTS_DIR / "FjallaOne-Regular.ttf",
    _FONTS_DIR / "RobotoCondensed-Bold.ttf",
    _FONTS_DIR / "IBMPlexSansCondensed-Bold.ttf",
    _FONTS_DIR / "ArchivoNarrow-Bold.ttf",
    _FONTS_DIR / "BebasNeue-Regular.ttf",
    # Technical / geometric
    _FONTS_DIR / "Rajdhani-Bold.ttf",
    _FONTS_DIR / "Oxanium-Bold.ttf",
    _FONTS_DIR / "ChakraPetch-Bold.ttf",
    _FONTS_DIR / "Exo2-Bold.ttf",
    _FONTS_DIR / "TitilliumWeb-Bold.ttf",
    _FONTS_DIR / "RussoOne-Regular.ttf",
    # More character / occasional
    _FONTS_DIR / "Anton-Regular.ttf",
    _FONTS_DIR / "Teko-SemiBold.ttf",
    _FONTS_DIR / "Bangers-Regular.ttfe",
    _FONTS_DIR / "ConcertOne-Regular.ttfe",
]


def _existing_fonts() -> list[Path]:
    fonts = [path for path in _FONT_PATHS if path.exists()]

    if not fonts:
        raise FileNotFoundError(f"No thumbnail fonts found in {_FONTS_DIR}. " "Expected at least one TTF font.")

    return fonts


# ---------------------------------------------------------------------------
# Text layout
# ---------------------------------------------------------------------------


def _wrap_candidates(
    words: list[str],
    max_lines: int = 3,
):
    """
    Yield possible 1-3 line splits.

    Thumbnail titles are short enough that trying each possible
    split is cheap, and produces much nicer wrapping than textwrap.
    """
    if not words:
        yield [""]
        return

    # One line
    yield [" ".join(words)]

    # Two lines
    if max_lines >= 2:
        for i in range(1, len(words)):
            yield [
                " ".join(words[:i]),
                " ".join(words[i:]),
            ]

    # Three lines
    if max_lines >= 3:
        for i in range(1, len(words) - 1):
            for j in range(i + 1, len(words)):
                yield [
                    " ".join(words[:i]),
                    " ".join(words[i:j]),
                    " ".join(words[j:]),
                ]


def _fit_title(
    draw: PIL.ImageDraw.ImageDraw,
    title: str,
    font_path: Path,
    max_width: int,
    max_height: int,
    image_height: int,
    align: str,
) -> tuple[
    PIL.ImageFont.FreeTypeFont,
    str,
    int,
]:
    """
    Find the largest font size and the most balanced 1-3 line
    wrapping that fits the available region.

    This uses rendered pixel dimensions rather than character count.
    """
    words = title.split() or [title]

    if len(title) <= 18:
        max_font_size = int(image_height * 0.34)
    else:
        max_font_size = int(image_height * 0.28)

    min_font_size = max(
        22,
        int(image_height * 0.075),
    )

    for font_size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):
        font = PIL.ImageFont.truetype(
            font_path.as_posix(),
            font_size,
        )

        spacing = max(
            4,
            round(font_size * 0.10),
        )

        fitting = []

        for lines in _wrap_candidates(
            words,
            max_lines=3,
        ):
            rendered = "\n".join(lines)

            bbox = draw.multiline_textbbox(
                (0, 0),
                rendered,
                font=font,
                spacing=spacing,
                align=align,
            )

            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]

            if width > max_width:
                continue

            if height > max_height:
                continue

            line_widths = [
                draw.textbbox(
                    (0, 0),
                    line,
                    font=font,
                )[2]
                for line in lines
            ]

            mean_width = sum(line_widths) / len(line_widths)

            raggedness = sum(abs(width - mean_width) for width in line_widths)

            # Balanced wrapping matters, but prefer fewer lines
            # slightly when two choices look similarly good.
            score = raggedness + (len(lines) - 1) * max_width * 0.08

            fitting.append((score, rendered))

        if fitting:
            _, rendered = min(
                fitting,
                key=lambda item: item[0],
            )

            return (
                font,
                rendered,
                spacing,
            )

    # Emergency fallback for a title containing one extremely
    # long word/token.
    font = PIL.ImageFont.truetype(
        font_path.as_posix(),
        min_font_size,
    )

    spacing = max(
        4,
        round(min_font_size * 0.10),
    )

    rendered = title

    while rendered:
        candidate = rendered.rstrip() + ("..." if rendered != title else "")

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if bbox[2] - bbox[0] <= max_width:
            return (
                font,
                candidate,
                spacing,
            )

        rendered = rendered[:-1]

    return (
        font,
        "...",
        spacing,
    )
