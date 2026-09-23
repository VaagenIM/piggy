"""Base types for object-oriented thumbnail backgrounds."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random

import PIL.Image


RGB = tuple[int, int, int]


@dataclass(frozen=True)
class ThumbnailPalette:
    """A curated, coordinated colour family."""

    backgrounds: tuple[str, ...]
    text: str
    accent: str


@dataclass
class BackgroundContext:
    """All inputs a background style needs to render itself."""

    size: tuple[int, int]
    palette: ThumbnailPalette
    layout: str
    rng: random.Random


class BackgroundStyle(ABC):
    """Base class for one procedural background composition."""

    name: str
    weight: float = 1.0
    complexity: int = 0

    @abstractmethod
    def draw(self, ctx: BackgroundContext) -> PIL.Image.Image:
        """Render this background."""
        raise NotImplementedError
