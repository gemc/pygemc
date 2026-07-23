#!/usr/bin/env python3
"""Remove drilled through-holes (bolt holes) from a CAD mesh for Geant4.

Fabrication CAD of support structures (e.g. the LTCC aluminium frame plates) carries dozens of
bolt holes. In a watertight mesh each drilled hole is not an *open* hole but a **tunnel** — a
handle that raises the surface genus — so :func:`~pygemc.utilities.cure_mesh.cure_mesh`'s
close-holes step cannot touch it (a tunnel has no boundary edge). The holes are irrelevant to a
Geant4 simulation of the frame yet slow the tessellated solid down and clutter the picture.

:func:`remove_holes` fills the tunnels flush with the surrounding surface:

  1. a bolt tunnel is a short cylindrical band of facets whose normals are perpendicular to the
     drill axis; the band's cross-section (its extent in the plane perpendicular to that axis) is
     small — the bolt diameter. For each of the three axes, the mesh's "wall" facets (normal
     roughly perpendicular to the axis) are grouped into connected components, and every component
     whose in-plane diameter is below ``max_hole_diameter`` is a bolt tunnel (or a small edge
     notch);
  2. those facets are deleted, which turns each tunnel into two small boundary loops (its rims);
  3. a manifold-repair / close-holes pass caps the loops, so the plate becomes solid where the
     bolt used to pass through. The large outer rim is never a small component, so the plate
     silhouette is preserved and its bounding box is unchanged.

This deliberately does **not** touch large openings: a Winston cone's aperture or a plate's outline
is not a small-diameter wall component, so pass such meshes through :func:`cure_mesh` instead.
"""

import argparse
import os
import sys
from collections import defaultdict


def _wall_faces_to_drop(vertices, faces, max_hole_diameter, wall_cos):
    """Return the set of facet indices belonging to small (bolt-sized) wall components.

    For each axis, facets whose unit normal is within ``wall_cos`` of perpendicular to the axis are
    grouped into shared-edge connected components; a component is dropped when its extent in the
    plane perpendicular to the axis is smaller than ``max_hole_diameter``.
    """
    import numpy as np

    p0, p1, p2 = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    normals = np.cross(p1 - p0, p2 - p0)
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    normals /= lengths[:, None]

    drop = set()
    for axis in (0, 1, 2):
        plane = [i for i in range(3) if i != axis]
        wall = np.where(np.abs(normals[:, axis]) < wall_cos)[0]
        wall_set = set(wall.tolist())

        # Facet adjacency restricted to wall facets (share an edge).
        edge_to_faces = defaultdict(list)
        for fi in wall:
            a, b, c = faces[fi]
            for edge in ((a, b), (b, c), (c, a)):
                edge_to_faces[tuple(sorted(edge))].append(fi)
        adjacency = defaultdict(list)
        for shared in edge_to_faces.values():
            for i in range(len(shared)):
                for j in range(i + 1, len(shared)):
                    adjacency[shared[i]].append(shared[j])
                    adjacency[shared[j]].append(shared[i])

        seen = set()
        for start in wall:
            if start in seen:
                continue
            stack, component = [start], []
            while stack:
                fi = stack.pop()
                if fi in seen:
                    continue
                seen.add(fi)
                component.append(fi)
                stack.extend(adjacency[fi])
            verts = np.unique(faces[component].ravel())
            points = vertices[verts][:, plane]
            if np.linalg.norm(points.max(0) - points.min(0)) < max_hole_diameter:
                drop.update(component)
    return drop


def _repair_and_close(ms, iterations):
    """Weld cracks, split non-manifold edges/vertices, then cap the small openings left behind."""
    import pymeshlab as ml

    def try_filter(name, **kwargs):
        try:
            getattr(ms, name)(**kwargs)
        except ml.PyMeshLabException:
            pass

    ms.meshing_merge_close_vertices(threshold=ml.PercentageValue(0.1))
    for _ in range(max(1, iterations)):
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_null_faces()
        ms.meshing_repair_non_manifold_edges(method='Remove Faces')
        try_filter("meshing_repair_non_manifold_vertices")
        ms.meshing_remove_unreferenced_vertices()
        try_filter("meshing_close_holes", maxholesize=100000, selfintersection=False)
    try_filter("meshing_re_orient_faces_coherently")

    measures = ms.get_geometric_measures()
    volume = measures.get('mesh_volume')
    if volume is not None and volume < 0:
        ms.meshing_invert_face_orientation()


def remove_holes(input_path, output_path=None, max_hole_diameter=40.0, wall_cos=0.5,
                 close_iterations=6, verbose=True):
    """Fill drilled through-holes (bolt holes) in a mesh, returning before/after statistics.

    Parameters
    ----------
    input_path : str
        Mesh file to read. Best run on an already-cured mesh (see :func:`cure_mesh`).
    output_path : str, optional
        Where to write the result. Defaults to ``input_path`` (in-place overwrite).
    max_hole_diameter : float
        Wall components smaller than this (in mesh units, usually mm) across the perpendicular plane
        are treated as bolt holes and filled. Keep it below the smallest real opening you want to
        preserve.
    wall_cos : float
        A facet is a "wall" for an axis when ``|normal . axis| < wall_cos`` (0.5 ≈ within 30° of
        perpendicular).
    close_iterations : int
        Manifold-repair / close-holes passes after deleting the bolt-hole walls.
    verbose : bool
        Print a one-line summary.

    Returns
    -------
    dict
        ``{"genus_in", "genus_out", "faces_in", "faces_out", "boundary_edges", "watertight"}``.
    """
    import numpy as np
    import pymeshlab as ml

    ms = ml.MeshSet()
    ms.load_new_mesh(str(input_path))
    genus_in = ms.get_topological_measures().get('genus')
    faces_in = ms.current_mesh().face_number()

    vertices = ms.current_mesh().vertex_matrix()
    faces = ms.current_mesh().face_matrix()
    drop = _wall_faces_to_drop(vertices, faces, max_hole_diameter, wall_cos)

    if drop:
        keep = np.array([i for i in range(len(faces)) if i not in drop])
        ms = ml.MeshSet()
        ms.add_mesh(ml.Mesh(vertices, faces[keep]))
    _repair_and_close(ms, close_iterations)

    topo = ms.get_topological_measures()
    genus_out = topo.get('genus')
    boundary_edges = topo.get('boundary_edges')

    if output_path is None:
        output_path = input_path
    ms.save_current_mesh(str(output_path))

    stats = {
        "genus_in": genus_in,
        "genus_out": genus_out,
        "faces_in": faces_in,
        "faces_out": ms.current_mesh().face_number(),
        "boundary_edges": boundary_edges,
        "watertight": boundary_edges == 0,
    }
    if verbose:
        tight = "watertight" if stats["watertight"] else f"{boundary_edges} boundary edges"
        print(f"  {os.path.basename(str(input_path)):26s} genus {genus_in:>3d} -> {genus_out:<3d} "
              f"({len(drop)} facets removed, {tight})")
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fill drilled through-holes (bolt holes) in a CAD mesh for Geant4.")
    parser.add_argument("input", help="input mesh (stl/ply/obj/...)")
    parser.add_argument("-o", "--output", default=None,
                        help="output mesh (default: overwrite the input)")
    parser.add_argument("-d", "--max-hole-diameter", type=float, default=40.0,
                        help="fill wall components smaller than this (mesh units). Default 40")
    parser.add_argument("--wall-cos", type=float, default=0.5,
                        help="normal-vs-axis perpendicularity threshold. Default 0.5 (~30 deg)")
    parser.add_argument("--close-iterations", type=int, default=6,
                        help="manifold-repair / close-holes passes. Default 6")
    args = parser.parse_args(argv)

    try:
        import pymeshlab  # noqa: F401
    except ImportError:
        sys.exit("Error: pymeshlab is required for remove_holes. Install it with 'pip install pymeshlab'.")

    remove_holes(args.input, args.output, max_hole_diameter=args.max_hole_diameter,
                 wall_cos=args.wall_cos, close_iterations=args.close_iterations)


if __name__ == "__main__":
    main()
