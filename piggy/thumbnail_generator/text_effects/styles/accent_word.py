import PIL.ImageDraw

from ..analysis import clean_word
from ..base import TextEffectContext, TextRenderContext, TextRenderState, TextStyle, TitleLayout
from ..helpers import line_positions


def draw_accent_word(
    draw: PIL.ImageDraw.ImageDraw,
    layout: TitleLayout,
    words: list[str],
    word_index: int,
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> bool:
    lines = layout.lines
    target = words[word_index]

    counter = 0
    line_no = word_no = None
    line_words: list[str] = []

    for i, line in enumerate(lines):
        line_words = line.split(" ")

        if counter + len(line_words) > word_index:
            line_no = i
            word_no = word_index - counter
            break

        counter += len(line_words)

    if line_no is None or clean_word(line_words[word_no]) != clean_word(target):
        return False

    draw.multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*text, 255),
        spacing=layout.spacing,
        align=layout.align,
    )

    line_left, line_top = line_positions(
        draw,
        lines,
        layout.font,
        layout.spacing,
        layout.align,
        layout.text_x,
        layout.text_y,
    )[line_no]

    prefix = " ".join(line_words[:word_no])
    if word_no > 0:
        prefix += " "

    word_x = line_left + draw.textlength(prefix, font=layout.font)

    draw.text(
        (word_x, line_top),
        line_words[word_no],
        font=layout.font,
        fill=(*accent, 255),
    )
    return True


class AccentWordStyle(TextStyle):
    name = "accent_word"
    self_contained = True

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        if not has_accent_word:
            return 0.0

        if ctx.accent_background_contrast < 3.0:
            return 0.0

        if ctx.local_background_variance > 0.20:
            return 0.0

        score = 3.0

        if 2 <= ctx.word_count <= 5:
            score += 2.5
        elif ctx.word_count > 8:
            score -= 2.0

        if ctx.line_count <= 2:
            score += 2.0
        else:
            score -= 1.5

        if ctx.layout == "center":
            score += 1.0

        if ctx.accent_background_contrast >= 4.5:
            score += 1.5

        return max(0.0, score)

    def draw_foreground(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        if ctx.accent_word_index is None:
            return

        placed = draw_accent_word(
            PIL.ImageDraw.Draw(state.image),
            ctx.layout,
            ctx.words,
            ctx.accent_word_index,
            state.foreground_color,
            ctx.accent,
        )
        state.foreground_drawn = placed
