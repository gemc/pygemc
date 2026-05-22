"""pygemc.api — geometry, material, and configuration building blocks."""

from .gvolume import GVolume
from .gmaterial import GMaterial
from .gconfiguration import GConfiguration, autogeometry
from .gutils import GColors
from .g4_units import convert_list, convert_length, convert_angle, convert_time, convert_energy
from .gsqlite import create_sqlite_database, populate_sqlite_geometry, populate_sqlite_materials
from .gcolors import pyvista_color_to_hex
from .solids_map import AVAILABLE_SOLIDS_MAP

__all__ = [
    "GVolume",
    "GMaterial",
    "GConfiguration",
    "autogeometry",
    "GColors",
    "convert_list",
    "convert_length",
    "convert_angle",
    "convert_time",
    "convert_energy",
    "create_sqlite_database",
    "populate_sqlite_geometry",
    "populate_sqlite_materials",
    "pyvista_color_to_hex",
    "AVAILABLE_SOLIDS_MAP",
]
