"""Subprocess worker performing pymeshlab boolean operations.

pymeshlab bundles its own Qt5 frameworks, which crash when loaded into the same process
as PyQt6 (used by the pyvistaqt background plotter, ``-pvb``). The boolean operations
therefore run in this dedicated worker process: the parent sends length-prefixed pickled
requests on stdin and reads the results from stdout.

This module must stay importable without pymeshlab: the parent imports it for the
message helpers, and pymeshlab is only imported inside :func:`main`.
"""

import os
import pickle
import struct
import sys


def read_msg(stream):
	"""Read one length-prefixed pickled message; return None on EOF."""
	header = stream.read(4)
	if len(header) < 4:
		return None
	(length,) = struct.unpack('>I', header)
	payload = stream.read(length)
	if len(payload) < length:
		return None
	return pickle.loads(payload)


def write_msg(stream, obj):
	"""Write one length-prefixed pickled message."""
	payload = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
	stream.write(struct.pack('>I', len(payload)))
	stream.write(payload)
	stream.flush()


def _add_oriented(ms, pymeshlab, verts, faces):
	# repair revolution/extrusion artifacts (duplicate seam vertices, degenerate axis
	# faces) so the operand is watertight, then orient the facets coherently and
	# outward (negative signed volume means inward-facing): the boolean arrangement
	# respects facet orientation
	ms.add_mesh(pymeshlab.Mesh(verts, faces))
	ms.meshing_remove_duplicate_vertices()
	ms.meshing_remove_duplicate_faces()
	ms.meshing_remove_null_faces()
	ms.meshing_remove_unreferenced_vertices()
	ms.meshing_repair_non_manifold_edges(method='Remove Faces')
	ms.meshing_close_holes(maxholesize=100, selfintersection=False)
	ms.meshing_re_orient_faces_coherently()
	if ms.get_geometric_measures().get('mesh_volume', 1.0) < 0:
		ms.meshing_invert_face_orientation()


def main():
	# Keep the protocol channel exclusive: move the process stdout to a private
	# descriptor and point fd 1 at stderr, so any pymeshlab/meshlab C++ printout
	# cannot corrupt the pickled message stream.
	protocol_out = os.fdopen(os.dup(1), 'wb')
	os.dup2(2, 1)
	sys.stdout = sys.stderr
	stdin = sys.stdin.buffer

	try:
		import pymeshlab
	except Exception:
		write_msg(protocol_out, {'status': 'no_pymeshlab'})
		return
	write_msg(protocol_out, {'status': 'ready'})

	filters = {
		'-': 'generate_boolean_difference',
		'+': 'generate_boolean_union',
		'*': 'generate_boolean_intersection',
	}

	while True:
		msg = read_msg(stdin)
		if msg is None:
			break
		try:
			op, va, fa, vb, fb = msg
			ms = pymeshlab.MeshSet()
			_add_oriented(ms, pymeshlab, va, fa)
			_add_oriented(ms, pymeshlab, vb, fb)
			getattr(ms, filters[op])(first_mesh=0, second_mesh=1)
			out = ms.current_mesh()
			if out.vertex_number() == 0 or out.face_number() == 0:
				write_msg(protocol_out, None)
			else:
				write_msg(protocol_out, (out.vertex_matrix(), out.face_matrix()))
		except Exception:
			write_msg(protocol_out, None)


if __name__ == '__main__':
	main()
