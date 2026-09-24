"""Backward-compatible public entry point for thumbnail generation.

The implementation now lives in :mod:`piggy.thumbnail_generator` so callers can
continue importing ``piggy.thumbnails.create_thumbnail`` unchanged.
"""

from .thumbnail_generator import create_thumbnail

__all__ = ["create_thumbnail"]
