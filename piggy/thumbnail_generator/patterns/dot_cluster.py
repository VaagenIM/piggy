"""Edge-anchored dot-cluster ambient pattern."""

from .base import Pattern, PatternContext


class DotClusterPattern(Pattern):
    name = "dot_cluster"

    def draw(self, ctx: PatternContext) -> None:
        columns = ctx.rng.randint(7, 11)
        rows = ctx.rng.randint(5, 8)
        side = ctx.rng.choice(("left", "right"))

        area_w = int(ctx.w * 0.28)
        area_h = int(ctx.h * 0.65)

        if side == "left":
            start_x = 0
        else:
            start_x = ctx.w - area_w

        start_y = ctx.rng.randint(
            0,
            max(0, ctx.h - area_h),
        )

        cell_w = area_w / columns
        cell_h = area_h / rows

        for col in range(columns):
            for row in range(rows):
                cx = start_x + cell_w * (col + 0.5)
                cy = start_y + cell_h * (row + 0.5)

                progression = col / max(1, columns - 1)

                if side == "right":
                    progression = 1 - progression

                radius = max(
                    2,
                    min(cell_w, cell_h) * (0.08 + progression * 0.15),
                )

                ctx.draw.ellipse(
                    (
                        cx - radius,
                        cy - radius,
                        cx + radius,
                        cy + radius,
                    ),
                    fill=(*ctx.accent, 55),
                )
