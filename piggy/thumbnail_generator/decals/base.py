"""Base types for structural thumbnail decals."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random

import PIL.Image

BBox = tuple[int, int, int, int]
RGB = tuple[int, int, int]


@dataclass
class DecalContext:
    """Composition information used to decide whether a decal fits."""

    layout: str
    title_bbox: BBox
    line_count: int
    text_width_ratio: float
    text_height_ratio: float
    background_style: str
    background_complexity: int
    pattern_name: str | None
    w: int
    h: int


@dataclass
class DecalRenderContext:
    """Everything a decal needs while rendering itself."""

    layer: PIL.Image.Image
    w: int
    h: int
    accent: RGB
    secondary: RGB
    safe_bbox: BBox
    layout: str
    complexity: int
    rng: random.Random


@dataclass
class DecalResult:
    """Rendered layer plus the region occupied by the primary motif."""

    layer: PIL.Image.Image
    region: BBox | None


class Decal(ABC):
    """One self-contained structural decal family."""

    name: str
    pattern_conflicts: dict[str, float] = {}
    support_enabled: bool = True

    @abstractmethod
    def score(self, ctx: DecalContext) -> float:
        """Return this decal's contextual selection weight before pattern conflicts."""
        raise NotImplementedError

    def final_score(self, ctx: DecalContext) -> float:
        score = self.score(ctx)
        score *= self.pattern_conflicts.get(ctx.pattern_name, 1.0)
        return max(0.0, score)

    @abstractmethod
    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        """Render the primary motif."""
        raise NotImplementedError

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        """Render one optional supporting mini-decal near the primary motif."""
        return None
