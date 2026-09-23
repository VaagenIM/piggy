from ..base import IsolationTreatment, TextEffectContext


class NoIsolation(IsolationTreatment):
    name = "none"

    def score(self, ctx: TextEffectContext) -> float:
        score = 2.0

        if ctx.minimum_text_contrast >= 6.5 and ctx.local_background_variance < 0.05:
            score += 4.0
        elif ctx.minimum_text_contrast >= 5.0 and ctx.local_background_variance < 0.08:
            score += 2.0

        return score
