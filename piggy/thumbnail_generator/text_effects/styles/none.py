from ..base import TextEffectContext, TextStyle


class NoTextStyle(TextStyle):
    name = "none"

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        score = 6.0

        if ctx.line_count >= 3:
            score += 3.0

        if ctx.font_size_ratio < 0.14:
            score += 2.0

        if ctx.text_height_ratio > 0.75:
            score += 1.5

        return score
