"""The explicit no-decal candidate."""

from .base import Decal, DecalContext, DecalRenderContext, DecalResult


class NoDecal(Decal):
    name = "none"
    support_enabled = False

    def score(self, ctx: DecalContext) -> float:
        score = 4.0
        if ctx.line_count >= 3:
            score += 4.0
        if ctx.background_complexity >= 2:
            score += 1.5
        if ctx.text_width_ratio > 0.75:
            score += 1.5
        return score

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        return DecalResult(ctx.layer, None)
