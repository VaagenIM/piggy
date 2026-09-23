"""Base types for low-priority ambient thumbnail patterns."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random

import PIL.ImageDraw

RGB = tuple[int, int, int]


@dataclass
class PatternContext:
    """Everything an ambient pattern needs while rendering itself."""

    draw: PIL.ImageDraw.ImageDraw
    w: int
    h: int
    accent: RGB
    rng: random.Random


class Pattern(ABC):
    """One self-contained ambient pattern family."""

    name: str
    weight: float = 1.0

    @abstractmethod
    def draw(self, ctx: PatternContext) -> None:
        """Render this pattern into the supplied drawing context."""
        raise NotImplementedError
