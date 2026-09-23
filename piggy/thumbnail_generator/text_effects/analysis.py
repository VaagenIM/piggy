"""Background analysis and shared effect-selection utilities."""

from pathlib import Path
import random

import PIL.Image
import PIL.ImageFont

from ..common import _contrast_ratio, _relative_luminance
from .base import TextEffectContext


SHORT_STOPWORDS = {
    "og",
    "i",
    "på",
    "av",
    "en",
    "et",
    "er",
    "til",
    "for",
    "med",
    "som",
    "de",
    "det",
    "den",
    "du",
    "vi",
    "å",
    "om",
    "ikke",
    "har",
    "a",
    "an",
    "the",
    "of",
    "to",
    "in",
    "on",
    "at",
    "is",
    "it",
    "and",
    "or",
    "as",
    "by",
    "be",
    "are",
    "was",
}


def clean_word(word: str) -> str:
    return word.strip(".,:;!?()[]{}'\"«»“”‘’-–—").lower()


def select_accent_word_index(words: list[str], effect_rng: random.Random) -> int | None:
    def candidates(min_length: int) -> list[int]:
        return [
            i
            for i, word in enumerate(words)
            if len(clean_word(word)) >= min_length and clean_word(word) not in SHORT_STOPWORDS
        ]

    picks = candidates(4) or candidates(3)
    return effect_rng.choice(picks) if picks else None


def analyze_text_background(
    image: PIL.Image.Image,
    decoration: PIL.Image.Image,
    box: tuple[int, int, int, int],
    text: tuple[int, int, int],
    w: int,
    h: int,
    cols: int = 6,
    rows: int = 3,
) -> tuple[float, float, float, float]:
    left, top, right, bottom = box
    pad_x = max(4, round((right - left) * 0.08))
    pad_y = max(4, round((bottom - top) * 0.15))

    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(w, right + pad_x)
    bottom = min(h, bottom + pad_y)

    rgb_pixels = image.convert("RGB").load()
    alpha_pixels = decoration.getchannel("A").load()

    luminances = []
    alphas = []
    min_contrast = float("inf")

    for row in range(rows):
        for col in range(cols):
            x = min(w - 1, max(0, int(left + (right - left) * (col + 0.5) / cols)))
            y = min(h - 1, max(0, int(top + (bottom - top) * (row + 0.5) / rows)))

            sample = rgb_pixels[x, y]
            luminances.append(_relative_luminance(sample))
            min_contrast = min(min_contrast, _contrast_ratio(text, sample))
            alphas.append(alpha_pixels[x, y])

    avg_luminance = sum(luminances) / len(luminances)
    luminance_range = max(luminances) - min(luminances)
    pattern_density = (sum(alphas) / len(alphas)) / 255

    return avg_luminance, luminance_range, min_contrast, pattern_density


def build_text_effect_context(
    *,
    layout: str,
    font_path: Path,
    font: PIL.ImageFont.FreeTypeFont,
    words: list[str],
    rendered_text: str,
    text_w: int,
    text_h: int,
    w: int,
    h: int,
    background: tuple[int, int, int],
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    local_luminance: float,
    local_variance: float,
    local_min_contrast: float,
    pattern_density: float,
) -> TextEffectContext:
    return TextEffectContext(
        layout=layout,
        font_path=font_path,
        font_size=font.size,
        font_size_ratio=font.size / h,
        line_count=rendered_text.count("\n") + 1,
        word_count=len(words),
        text_width_ratio=text_w / w,
        text_height_ratio=text_h / h,
        background_luminance=_relative_luminance(background),
        local_background_luminance=local_luminance,
        local_background_variance=local_variance,
        minimum_text_contrast=local_min_contrast,
        accent_background_contrast=_contrast_ratio(accent, background),
        accent_text_contrast=_contrast_ratio(accent, text),
        pattern_density=pattern_density,
    )


def quiet_panel_alpha(ctx: TextEffectContext) -> int:
    if ctx.minimum_text_contrast >= 7.0 and ctx.local_background_variance < 0.04:
        return 0

    strength = min(1.0, ctx.local_background_variance / 0.30) * 0.6
    strength += min(1.0, ctx.pattern_density) * 0.4

    if ctx.minimum_text_contrast < 4.5:
        strength = max(strength, 0.55)

    strength = min(1.0, strength)
    return round(35 + strength * 100)
