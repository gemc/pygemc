"""pygemc.utilities — offline helpers that are not part of the geometry-definition API.

Currently provides :func:`cure_mesh`, which simplifies and repairs CAD (STL/PLY/OBJ...) meshes so
that Geant4's ``G4TessellatedSolid`` loads them quickly and without "holes / wrong orientation /
negative volume" warnings.
"""

from .cure_mesh import cure_mesh

__all__ = ["cure_mesh"]
