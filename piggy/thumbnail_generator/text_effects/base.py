"""Base types for object-oriented title effects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import random

import PIL.Image
import PIL.ImageFont


RGB = tuple[int, int, int]
BBox = tuple[int, int, int, int]


@dataclass
class TitleLayout:
    """Everything an effect needs to redraw the already-fitted title."""

    font: PIL.ImageFont.FreeTypeFont
    rendered_text: str
    spacing: int
    align: str
    text_x: int
    text_y: int
    text_bbox: BBox

    @property
    def lines(self) -> list[str]:
        return self.rendered_text.split("\n")


@dataclass
class TextEffectContext:
    """Measured composition context used to score title effects."""

    layout: str
    font_path: Path
    font_size: int
    font_size_ratio: float
    line_count: int
    word_count: int
    text_width_ratio: float
    text_height_ratio: float
    background_luminance: float
    local_background_luminance: float
    local_background_variance: float
    minimum_text_contrast: float
    accent_background_contrast: float
    accent_text_contrast: float
    pattern_density: float


@dataclass
class TextRenderContext:
    """Inputs shared by all isolation/style renderers."""

    layout: TitleLayout
    w: int
    h: int
    text: RGB
    accent: RGB
    background: RGB
    words: list[str]
    accent_word_index: int | None
    rng: random.Random


@dataclass
class TextRenderState:
    """Mutable state passed through isolation and stylistic layers."""

    image: PIL.Image.Image
    foreground_color: RGB
    foreground_drawn: bool = False


class IsolationTreatment(ABC):
    name: str
    suppresses_style: bool = False
    rejects_self_contained_style: bool = False

    @abstractmethod
    def score(self, ctx: TextEffectContext) -> float:
        raise NotImplementedError

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        return

    def draw_foreground(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        return


class TextStyle(ABC):
    name: str
    self_contained: bool = False

    @abstractmethod
    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        raise NotImplementedError

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        return

    def draw_foreground(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        return
