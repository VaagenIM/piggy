"""Explicit decal registry and context-aware selection."""

import random

from ..common import _weighted_choice
from .base import Decal, DecalContext
from .none import NoDecal
from .node_graph import NodeGraphDecal
from .orbit_cluster import OrbitClusterDecal
from .side_panel import SidePanelDecal
from .badge import BadgeDecal
from .corner_frame import CornerFrameDecal
from .ribbon import RibbonDecal
from .circuit_trace import CircuitTraceDecal
from .isometric_cubes import IsometricCubesDecal
from .signal_wave import SignalWaveDecal
from .blueprint_measure import BlueprintMeasureDecal
from .hex_cluster import HexClusterDecal


DECALS: tuple[Decal, ...] = (
    NoDecal(),
    NodeGraphDecal(),
    OrbitClusterDecal(),
    SidePanelDecal(),
    BadgeDecal(),
    CornerFrameDecal(),
    RibbonDecal(),
    CircuitTraceDecal(),
    IsometricCubesDecal(),
    SignalWaveDecal(),
    BlueprintMeasureDecal(),
    HexClusterDecal(),
)

DECALS_BY_NAME: dict[str, Decal] = {decal.name: decal for decal in DECALS}


def choose_primary_decal(ctx: DecalContext, rng: random.Random) -> Decal:
    scores = {decal.name: decal.final_score(ctx) for decal in DECALS}
    name = _weighted_choice(scores, rng)
    return DECALS_BY_NAME[name]
