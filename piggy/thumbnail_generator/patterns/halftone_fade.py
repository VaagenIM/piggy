from .base import Pattern, PatternContext


class HalftoneFadePattern(Pattern):
    name = "halftone_fade"

    def draw(
        self,
        ctx: PatternContext,
    ) -> None:
        side = ctx.rng.choice(("left", "right"))

        spacing = ctx.rng.randint(
            max(18, ctx.w // 55),
            max(28, ctx.w // 40),
        )

        rows = ctx.h // spacing + 2

        cols = ctx.w // spacing + 2

        max_radius = ctx.rng.uniform(
            2.5,
            5.0,
        )

        start_strength = ctx.rng.uniform(
            0.65,
            0.95,
        )

        fade_width = ctx.rng.uniform(
            0.28,
            0.48,
        )

        for row in range(rows):
            y = row * spacing + spacing / 2

            # Stagger alternate rows.
            row_shift = spacing / 2 if row % 2 else 0

            for col in range(cols):
                x = col * spacing + row_shift

                position = x / max(
                    1,
                    ctx.w,
                )

                if side == "right":
                    position = 1.0 - position

                strength = start_strength - position / fade_width

                strength = max(
                    0.0,
                    min(
                        1.0,
                        strength,
                    ),
                )

                if strength <= 0:
                    continue

                # Slight random thinning keeps the edge
                # from looking mathematically clipped.
                if ctx.rng.random() > 0.55 + strength * 0.40:
                    continue

                radius = max(
                    1.0,
                    max_radius * strength,
                )

                alpha = round(22 + strength * 48)

                ctx.draw.ellipse(
                    (
                        x - radius,
                        y - radius,
                        x + radius,
                        y + radius,
                    ),
                    fill=(
                        *ctx.accent,
                        alpha,
                    ),
                )
