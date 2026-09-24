"""Explicit ambient-pattern registry."""

from .base import Pattern
from .rings import RingsPattern
from .grid import GridPattern
from .diagonal_blocks import DiagonalBlocksPattern
from .dot_cluster import DotClusterPattern
from .waves import WavesPattern
from .corner_geometry import CornerGeometryPattern
from .topographic_contours import TopographicContoursPattern
from .micro_dashes import MicroDashesPattern
from .broken_grid import BrokenGridPattern
from .halftone_fade import HalftoneFadePattern


# Keep this order stable: renderer selection intentionally preserves the old
# `(style_seed // 7) % len(patterns)` behaviour.
PATTERNS = (
    RingsPattern(),
    GridPattern(),
    DiagonalBlocksPattern(),
    DotClusterPattern(),
    WavesPattern(),
    CornerGeometryPattern(),
    TopographicContoursPattern(),
    MicroDashesPattern(),
    BrokenGridPattern(),
    HalftoneFadePattern(),
)

PATTERNS_BY_NAME: dict[str, Pattern] = {pattern.name: pattern for pattern in PATTERNS}
