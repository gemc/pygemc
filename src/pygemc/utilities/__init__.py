"""pygemc.utilities — offline helpers that are not part of the geometry-definition API.

Provides:

- :func:`cure_mesh`, which simplifies and repairs CAD (STL/PLY/OBJ...) meshes so that Geant4's
  ``G4TessellatedSolid`` loads them quickly and without "holes / wrong orientation / negative
  volume" warnings;
- :func:`remove_holes`, which fills drilled through-holes (bolt holes) — surface tunnels that
  cure_mesh cannot close — flush with the surrounding surface.
"""

from .cure_mesh import cure_mesh
from .remove_holes import remove_holes

__all__ = ["cure_mesh", "remove_holes"]
