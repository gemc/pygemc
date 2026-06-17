"""pygemc — Python API for GEMC geometry definition and output analysis."""

from .api import (
    GVolume,
    GMaterial,
    GConfiguration,
    GColors,
    autogeometry,
    convert_list,
    convert_length,
    convert_angle,
    convert_time,
    convert_energy,
)

# Analyzer names are deferred so geometry-only scripts don't pay the cost
# of importing pandas / matplotlib / pyvistaqt at startup.
_ANALYZER_NAMES = {"GemcOutput", "available_variables", "plot_variable", "read_output"}

__all__ = [
    "GVolume",
    "GMaterial",
    "GConfiguration",
    "GColors",
    "autogeometry",
    "convert_list",
    "convert_length",
    "convert_angle",
    "convert_time",
    "convert_energy",
    "GemcOutput",
    "available_variables",
    "plot_variable",
    "read_output",
]


def __getattr__(name: str):
    if name in _ANALYZER_NAMES:
        from . import analyzer as _analyzer
        return getattr(_analyzer, name)
    raise AttributeError(f"module 'pygemc' has no attribute {name!r}")
