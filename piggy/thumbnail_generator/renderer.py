"""High-level thumbnail composition pipeline."""

import random

import PIL.Image
import PIL.ImageDraw

from piggy.utils import lru_cache_wrapper

from .backgrounds import (
    BackgroundContext,
    choose_background_style,
    choose_palette,
    pattern_strength,
    scale_layer_alpha,
    synthetic_palette_from_background,
)
from .common import _ensure_text_contrast, _hex_to_rgb, _seed_from_text
from .decals import (
    _DecalContext,
    _choose_primary_decal,
    _expand_bbox,
    _render_primary_decal,
    _render_supporting_decals,
)
from .patterns import PATTERNS, PatternContext
from .text_effects import (
    TextRenderContext,
    TitleLayout,
    analyze_text_background,
    build_text_effect_context,
    choose_isolation_treatment,
    choose_text_style,
    quiet_panel_alpha,
    reconcile_effects,
    render_title,
    select_accent_word_index,
)
from .typography import _existing_fonts, _fit_title

# ---------------------------------------------------------------------------
# Thumbnail renderer
# ---------------------------------------------------------------------------


@lru_cache_wrapper
def create_thumbnail(
    title: str,
    bg_color: str | None = None,
    text_color: str | None = None,
    size: tuple[int, int] = (800, 250),
    seed: str = "",
) -> PIL.Image.Image:
    """
    Create a deterministic fallback thumbnail.

    `seed` controls the visual style independently from the
    visible title.

    This means that `c` can later represent a module/category
    without requiring another rewrite of the renderer.

    `bg_color`/`text_color` are manual overrides (as `rrggbb` hex,
    no `#`); `api.py` is responsible for reading/sanitizing query
    params and passes `None` through when none was supplied. With no
    override, a curated `_ThumbnailPalette` supplies background,
    text, and accent colour as one coordinated family. With a manual
    `bg_color`, that colour becomes the base of a synthetic family
    (`_synthetic_palette_from_background`) instead -- the request is
    read, never silently replaced -- and the accent falls back to
    `_accent_from_background`.
    """
    w, h = size

    title = (
        " ".join(
            title.split()
        ).strip()
        or "Untitled"
    )

    style_seed = _seed_from_text(
        title,
        seed or title,
    )

    background_rng = random.Random(
        style_seed ^ 0xB4C6C0DE
    )

    pattern_rng = random.Random(
        style_seed ^ 0x9A11E4D9
    )

    if bg_color is not None:
        palette = synthetic_palette_from_background(
            _hex_to_rgb(bg_color),
            style_seed,
        )
    else:
        palette = choose_palette(
            style_seed
        )

    background = _hex_to_rgb(
        palette.backgrounds[0]
    )

    requested_text = _hex_to_rgb(
        text_color
        if text_color is not None
        else palette.text
    )

    # Guarantee readable typography.
    text = _ensure_text_contrast(
        requested_text,
        background,
    )

    accent = _hex_to_rgb(
        palette.accent
    )

    layout = (
        "center"
        if style_seed % 3
        else "left"
    )

    background_style = choose_background_style(
        background_rng
    )

    image = background_style.draw(
        BackgroundContext(
            size=size,
            palette=palette,
            layout=layout,
            rng=background_rng,
        )
    )

    # ------------------------------------------------------------
    # Decorative pattern
    # ------------------------------------------------------------

    decoration = PIL.Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0),
    )

    decoration_draw = (
        PIL.ImageDraw.Draw(
            decoration
        )
    )

    pattern = PATTERNS[
        (style_seed // 7)
        % len(PATTERNS)
    ]

    pattern.draw(
        PatternContext(
            draw=decoration_draw,
            w=w,
            h=h,
            accent=accent,
            rng=pattern_rng,
        )
    )

    decoration = scale_layer_alpha(
        decoration,
        pattern_strength(background_style),
    )

    image = PIL.Image.alpha_composite(
        image,
        decoration,
    )

    measure_draw = PIL.ImageDraw.Draw(
        image
    )

    fonts = _existing_fonts()

    font_path = fonts[
        style_seed
        % len(fonts)
    ]

    if layout == "left":
        text_area_left = int(
            w * 0.10
        )

        text_area_right = int(
            w * 0.72
        )

        align = "left"

    else:
        text_area_left = int(
            w * 0.10
        )

        text_area_right = int(
            w * 0.90
        )

        align = "center"

    text_area_top = int(
        h * 0.12
    )

    text_area_bottom = int(
        h * 0.88
    )

    max_text_w = (
        text_area_right
        - text_area_left
    )

    max_text_h = (
        text_area_bottom
        - text_area_top
    )

    font, rendered_text, spacing = _fit_title(
        measure_draw,
        title,
        font_path,
        max_text_w,
        max_text_h,
        h,
        align,
    )

    local_bbox = (
        measure_draw.multiline_textbbox(
            (0, 0),
            rendered_text,
            font=font,
            spacing=spacing,
            align=align,
        )
    )

    text_w = (
        local_bbox[2]
        - local_bbox[0]
    )

    text_h = (
        local_bbox[3]
        - local_bbox[1]
    )

    if layout == "left":
        text_x = (
            text_area_left
            - local_bbox[0]
        )

    else:
        text_x = (
            (w - text_w) // 2
            - local_bbox[0]
        )

    text_y = (
        (h - text_h) // 2
        - local_bbox[1]
    )

    text_bbox = (
        measure_draw.multiline_textbbox(
            (text_x, text_y),
            rendered_text,
            font=font,
            spacing=spacing,
            align=align,
        )
    )

    # ------------------------------------------------------------
    # Structural decals
    # ------------------------------------------------------------

    safe_bbox = _expand_bbox(
        text_bbox,
        max(28, round(w * 0.045)),
        max(20, round(h * 0.12)),
        w,
        h,
    )

    decal_rng = random.Random(
        style_seed ^ 0x6C0DEBA5
    )

    background_complexity = background_style.complexity

    decal_ctx = _DecalContext(
        layout=layout,
        title_bbox=text_bbox,
        line_count=rendered_text.count("\n") + 1,
        text_width_ratio=text_w / w,
        text_height_ratio=text_h / h,
        background_style=background_style.name,
        background_complexity=background_complexity,
        pattern_name=pattern.name,
        w=w,
        h=h,
    )

    primary_decal = _choose_primary_decal(
        decal_ctx,
        decal_rng,
    )

    secondary = _hex_to_rgb(
        palette.backgrounds[1]
        if len(palette.backgrounds) > 1
        else palette.backgrounds[0]
    )

    decal_layer = PIL.Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0),
    )

    decal_layer, decal_region = _render_primary_decal(
        decal_layer,
        primary_decal,
        w,
        h,
        accent,
        secondary,
        safe_bbox,
        layout,
        background_complexity,
        decal_rng,
    )

    decal_layer = _render_supporting_decals(
        decal_layer,
        primary_decal,
        decal_region,
        w,
        h,
        accent,
        safe_bbox,
        decal_rng,
    )

    image = PIL.Image.alpha_composite(
        image,
        decal_layer,
    )

    # Decals count toward "decoration nearby" for the text-effect
    # system's pattern-density signal too, not just the ambient
    # pattern -- see `_analyze_text_background`.
    decoration = PIL.Image.alpha_composite(
        decoration,
        decal_layer,
    )

    # ------------------------------------------------------------
    # Effect selection
    # ------------------------------------------------------------

    words = title.split() or [title]

    local_luminance, local_variance, local_min_contrast, pattern_density = (
        analyze_text_background(
            image,
            decoration,
            text_bbox,
            text,
            w,
            h,
        )
    )

    ctx = build_text_effect_context(
        layout=layout,
        font_path=font_path,
        font=font,
        words=words,
        rendered_text=rendered_text,
        text_w=text_w,
        text_h=text_h,
        w=w,
        h=h,
        background=background,
        text=text,
        accent=accent,
        local_luminance=local_luminance,
        local_variance=local_variance,
        local_min_contrast=local_min_contrast,
        pattern_density=pattern_density,
    )

    effect_rng = random.Random(
        style_seed ^ 0x5A17C0DE
    )

    accent_word_index = select_accent_word_index(
        words,
        effect_rng,
    )

    isolation = choose_isolation_treatment(
        ctx,
        effect_rng,
    )

    text_effect = choose_text_style(
        ctx,
        effect_rng,
        accent_word_index is not None,
    )

    isolation, text_effect = reconcile_effects(
        isolation,
        text_effect,
    )

    # ------------------------------------------------------------
    # Quiet area behind title
    # ------------------------------------------------------------

    if isolation.name != "highlight":
        quiet_alpha = quiet_panel_alpha(ctx)

        if quiet_alpha > 0:
            quiet = PIL.Image.new(
                "RGBA",
                size,
                (0, 0, 0, 0),
            )

            quiet_draw = PIL.ImageDraw.Draw(
                quiet
            )

            panel_pad_x = max(
                18,
                w // 45,
            )

            panel_pad_y = max(
                14,
                h // 24,
            )

            panel_box = (
                max(
                    0,
                    text_bbox[0] - panel_pad_x,
                ),
                max(
                    0,
                    text_bbox[1] - panel_pad_y,
                ),
                min(
                    w,
                    text_bbox[2] + panel_pad_x,
                ),
                min(
                    h,
                    text_bbox[3] + panel_pad_y,
                ),
            )

            quiet_draw.rounded_rectangle(
                panel_box,
                radius=max(
                    12,
                    h // 20,
                ),
                fill=(
                    *background,
                    quiet_alpha,
                ),
            )

            image = PIL.Image.alpha_composite(
                image,
                quiet,
            )

    draw = PIL.ImageDraw.Draw(
        image
    )

    # ------------------------------------------------------------
    # Accent near title
    # ------------------------------------------------------------

    if isolation.name != "highlight":
        if layout == "left":
            bar_w = max(
                5,
                w // 170,
            )

            gap = max(
                14,
                w // 70,
            )

            draw.rounded_rectangle(
                (
                    text_bbox[0]
                    - gap
                    - bar_w,

                    text_bbox[1],

                    text_bbox[0]
                    - gap,

                    text_bbox[3],
                ),
                radius=bar_w,
                fill=(
                    *accent,
                    235,
                ),
            )

        else:
            underline_w = min(
                int(text_w * 0.28),
                int(w * 0.16),
            )

            underline_h = max(
                4,
                h // 85,
            )

            underline_y = min(
                h
                - underline_h
                - 12,

                text_bbox[3]
                + max(
                    14,
                    h // 24,
                ),
            )

            draw.rounded_rectangle(
                (
                    w // 2
                    - underline_w // 2,

                    underline_y,

                    w // 2
                    + underline_w // 2,

                    underline_y
                    + underline_h,
                ),
                radius=underline_h,
                fill=(
                    *accent,
                    235,
                ),
            )

    # ------------------------------------------------------------
    # Title
    # ------------------------------------------------------------

    title_layout = TitleLayout(
        font=font,
        rendered_text=rendered_text,
        spacing=spacing,
        align=align,
        text_x=text_x,
        text_y=text_y,
        text_bbox=text_bbox,
    )

    image = render_title(
        image,
        isolation,
        text_effect,
        TextRenderContext(
            layout=title_layout,
            w=w,
            h=h,
            text=text,
            accent=accent,
            background=background,
            words=words,
            accent_word_index=accent_word_index,
            rng=effect_rng,
        ),
    )

    return image.convert("RGB")
