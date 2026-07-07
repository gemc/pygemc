#!/usr/bin/env python3
"""Simplify and repair CAD meshes for Geant4 tessellated solids.

Raw scanned/printed meshes (e.g. anatomical STLs from NIH 3D) are often heavy and are stored as
an unwelded triangle soup with inconsistent facet winding and small holes. Geant4's
``G4TessellatedSolid::SetSolidClosed()`` then reports "holes in the surface", "some facets have
wrong orientation" and "negative cubic volume", and the large facet count makes loading slow.

:func:`cure_mesh` uses `pymeshlab <https://pymeshlab.readthedocs.io>`_ (MeshLab's engine) to:

  1. weld coincident vertices and drop duplicate / null faces (turns the STL soup into a real,
     connected mesh);
  2. discard tiny disconnected components (scanning noise);
  3. decimate with quadric edge collapse down to a target facet count (fast loading);
  4. repair non-manifold edges and close holes so the surface is watertight;
  5. re-orient the facets coherently and flip the whole mesh if its signed volume is negative,
     so the normals point outward.

The decimation and repair do not change the bounding box appreciably, so any ``scale`` /
``position`` authored for the mesh elsewhere (e.g. a GEMC CAD definition) stays valid.
"""

import argparse
import os
import sys

# Filters that are known to raise (rather than crash) on messy input are wrapped; the pymeshlab
# exception type is resolved lazily together with the module.


def cure_mesh(input_path, output_path=None, target_faces=20000, merge_percent=0.1,
              min_component_faces=100, hole_iterations=4, remove_self_intersections=False,
              self_intersection_passes=3, reconstruct=None, poisson_depth=9, verbose=True):
    """Simplify and repair a mesh, returning a dict of before/after statistics.

    Parameters
    ----------
    input_path : str
        Mesh file to read (any format MeshLab understands: stl, ply, obj, ...).
    output_path : str, optional
        Where to write the cured mesh. Defaults to ``input_path`` (in-place overwrite).
    target_faces : int
        Target number of facets after quadric-edge-collapse decimation. Use 0 to skip decimation.
    merge_percent : float
        Vertex-welding threshold, as a percentage of the mesh bounding-box diagonal.
    min_component_faces : int
        Connected components with fewer facets than this are removed as noise.
    hole_iterations : int
        How many repair/close-holes passes to run (a few passes close nested/awkward holes).
    remove_self_intersections : bool
        When True, also delete self-intersecting facets and re-close the openings. This clears the
        last Geant4 "wrong orientation" defects on meshes that cure cleanly (e.g. the heart), but it
        is off by default: on heavily self-intersecting scans pymeshlab's self-intersection filter can
        fragment the mesh or abort the process, so enable it per mesh.
    self_intersection_passes : int
        Maximum self-intersection removal passes when ``remove_self_intersections`` is True.
    reconstruct : str, optional
        Set to ``"poisson"`` to rebuild the surface with screened Poisson reconstruction before
        decimation. This turns a fragmented, many-shell scan (dozens of components, large holes) into
        a single watertight manifold, at the cost of resampling the geometry. Best for badly broken
        meshes; leave ``None`` for meshes that clean up directly. Poisson can abort on very large or
        thin-walled meshes.
    poisson_depth : int
        Octree depth for the Poisson reconstruction (higher keeps more detail). Used only when
        ``reconstruct="poisson"``.
    verbose : bool
        Print a one-line summary.

    Returns
    -------
    dict
        ``{"faces_in", "faces_out", "volume", "boundary_edges", "watertight"}``.
    """
    import pymeshlab as ml

    ms = ml.MeshSet()
    ms.load_new_mesh(str(input_path))
    faces_in = ms.current_mesh().face_number()

    def try_filter(name, **kwargs):
        """Apply a filter, swallowing the (non-fatal) exceptions messy meshes can trigger."""
        try:
            getattr(ms, name)(**kwargs)
        except ml.PyMeshLabException as exc:
            if verbose:
                print(f"    (skipped {name}: {exc})")

    # 1. weld the triangle soup and drop degenerate/duplicate faces
    ms.meshing_merge_close_vertices(threshold=ml.PercentageValue(merge_percent))
    ms.meshing_remove_duplicate_faces()
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_remove_null_faces()
    ms.meshing_remove_unreferenced_vertices()

    # 2. drop scanning-noise islands
    if min_component_faces > 0:
        try_filter("meshing_remove_connected_component_by_face_number",
                   mincomponentsize=int(min_component_faces))

    # 2b. optional Poisson reconstruction: rebuild one watertight manifold from consistently
    #     oriented point-cloud normals. Turns a many-shell, holey scan into a single closed surface.
    if reconstruct == "poisson":
        ms.compute_normal_for_point_clouds(k=16, smoothiter=2)
        ms.generate_surface_reconstruction_screened_poisson(
            depth=int(poisson_depth), fulldepth=6, preclean=True, samplespernode=4.0)
        # Poisson can leave a low-density skirt as small extra components; keep the substantial ones.
        try_filter("meshing_remove_connected_component_by_face_number",
                   mincomponentsize=max(1000, int(min_component_faces)))

    # 3. decimate to the target facet count
    if target_faces and ms.current_mesh().face_number() > target_faces:
        ms.meshing_decimation_quadric_edge_collapse(
            targetfacenum=int(target_faces), preservenormal=True,
            planarquadric=True, autoclean=True)
        if min_component_faces > 0:
            try_filter("meshing_remove_connected_component_by_face_number",
                       mincomponentsize=int(min_component_faces))

    def repair_pass():
        # Weld cracks, split non-manifold edges and vertices, then close the resulting holes.
        # (never enable close_holes selfintersection: it can crash the engine).
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_null_faces()
        ms.meshing_repair_non_manifold_edges(method='Remove Faces')
        try_filter("meshing_repair_non_manifold_vertices")
        ms.meshing_remove_unreferenced_vertices()
        ms.meshing_close_holes(maxholesize=1000000, selfintersection=False)

    # 4. make it manifold (edges AND vertices) and watertight
    for _ in range(max(1, hole_iterations)):
        repair_pass()

    # 5. optionally delete self-intersecting facets and re-close the openings. Each pass removes the
    #    flagged facets; the following repair closes the small holes that leaves behind.
    if remove_self_intersections:
        for _ in range(max(0, self_intersection_passes)):
            try_filter("compute_selection_by_self_intersections_per_face")
            if ms.current_mesh().selected_face_number() == 0:
                break
            ms.meshing_remove_selected_faces()
            repair_pass()

    # 6. drop folded facets, then a final manifold repair before coherent, outward orientation.
    ms.meshing_remove_folded_faces()
    repair_pass()
    ms.meshing_repair_non_manifold_edges(method='Remove Faces')
    try_filter("meshing_re_orient_faces_coherently")

    # Orient outward when the mesh is watertight enough for pymeshlab to report a signed volume.
    # (A non-watertight mesh has no well-defined volume; Geant4 may still warn for it.)
    volume = ms.get_geometric_measures().get('mesh_volume')
    if volume is not None and volume < 0:
        ms.meshing_invert_face_orientation()
        volume = -volume

    topo = ms.get_topological_measures()
    boundary_edges = topo.get('boundary_edges')

    if output_path is None:
        output_path = input_path
    ms.save_current_mesh(str(output_path))

    faces_out = ms.current_mesh().face_number()
    stats = {
        "faces_in": faces_in,
        "faces_out": faces_out,
        "volume": volume,
        "boundary_edges": boundary_edges,
        "watertight": boundary_edges == 0,
    }
    if verbose:
        tight = "watertight" if stats["watertight"] else f"{boundary_edges} boundary edges"
        print(f"  {os.path.basename(str(input_path)):26s} {faces_in:>7d} -> {faces_out:>6d} "
              f"facets  ({tight})")
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Simplify and repair a CAD mesh for Geant4 tessellated solids.")
    parser.add_argument("input", help="input mesh (stl/ply/obj/...)")
    parser.add_argument("-o", "--output", default=None,
                        help="output mesh (default: overwrite the input)")
    parser.add_argument("-f", "--target-faces", type=int, default=20000,
                        help="target facet count for decimation (0 to skip). Default 20000")
    parser.add_argument("--min-component-faces", type=int, default=100,
                        help="remove connected components smaller than this. Default 100")
    parser.add_argument("--merge-percent", type=float, default=0.1,
                        help="vertex-weld threshold, %% of bbox diagonal. Default 0.1")
    parser.add_argument("--hole-iterations", type=int, default=4,
                        help="repair/close-holes passes. Default 4")
    parser.add_argument("--remove-self-intersections", action="store_true",
                        help="also delete self-intersecting facets (clears the last defects on "
                             "clean meshes; may fragment or crash on heavily broken scans)")
    parser.add_argument("--reconstruct", choices=["poisson"], default=None,
                        help="rebuild one watertight manifold before decimation (for fragmented scans)")
    parser.add_argument("--poisson-depth", type=int, default=9,
                        help="octree depth for --reconstruct poisson. Default 9")
    args = parser.parse_args(argv)

    try:
        import pymeshlab  # noqa: F401
    except ImportError:
        sys.exit("Error: pymeshlab is required for cure_mesh. Install it with 'pip install pymeshlab'.")

    cure_mesh(args.input, args.output, target_faces=args.target_faces,
              min_component_faces=args.min_component_faces, merge_percent=args.merge_percent,
              hole_iterations=args.hole_iterations,
              remove_self_intersections=args.remove_self_intersections,
              reconstruct=args.reconstruct, poisson_depth=args.poisson_depth)


if __name__ == "__main__":
    main()
