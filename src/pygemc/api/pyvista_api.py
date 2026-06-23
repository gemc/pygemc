from .g4_units import convert_list, convert_angle
import numpy as np
import warnings


def euler_matrix_zyx(deg_rx, deg_ry, deg_rz):
	"""
	Build a 3x3 rotation matrix from intrinsic ZYX Euler angles.
	Convention:
	  - rz about Z
	  - ry about Y
	  - rx about X
	Angles are in degrees.
	"""
	rx = np.deg2rad(deg_rx)
	ry = np.deg2rad(deg_ry)
	rz = np.deg2rad(deg_rz)

	cz, sz = np.cos(rz), np.sin(rz)
	cy, sy = np.cos(ry), np.sin(ry)
	cx, sx = np.cos(rx), np.sin(rx)

	# Rz
	Rz = np.array([
		[cz, -sz, 0.0],
		[sz, cz, 0.0],
		[0.0, 0.0, 1.0],
	])

	# Ry
	Ry = np.array([
		[cy, 0.0, sy],
		[0.0, 1.0, 0.0],
		[-sy, 0.0, cy],
	])

	# Rx
	Rx = np.array([
		[1.0, 0.0, 0.0],
		[0.0, cx, -sx],
		[0.0, sx, cx],
	])

	# intrinsic ZYX means: v_local -> Rx -> Ry -> Rz
	# matrix multiply in that order: R = Rz @ Ry @ Rx
	return Rx @ Ry @ Rz


def _axis_rotation_matrix(axis: str, angle_deg: float) -> np.ndarray:
	"""Return 3x3 rotation matrix for rotation of angle_deg degrees around axis ('x', 'y', 'z')."""
	c = np.cos(np.deg2rad(angle_deg))
	s = np.sin(np.deg2rad(angle_deg))
	if axis == 'x':
		return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)
	if axis == 'y':
		return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)
	if axis == 'z':
		return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)
	return np.eye(3)


def parse_rotation_string(rotation_str: str) -> np.ndarray:
	"""Parse a GEMC rotation string and return a 3×3 rotation matrix.

	Handles:
	  - Simple xyz order:    "10*deg, 45*deg, 30*deg"
	  - Ordered axes:        "ordered: zxy, 90*deg, 25*deg, 0*deg"
	  - Double rotation:     "doubleRotation: rx1, ry1, rz1, rx2, ry2, rz2"
	  - Compound (legacy):   "a1, a2, a3 + b1, b2, b3"

	For ordered strings the first angle corresponds to the first axis listed, etc.
	Rotations are intrinsic (each axis acts on the already-rotated frame).
	"""
	s = rotation_str.strip() if rotation_str else ''
	if not s or s.lower() == 'null':
		return np.eye(3)

	R = np.eye(3)
	for part in s.split(' + '):
		part = part.strip()
		if not part:
			continue

		if part.startswith('doubleRotation:'):
			tail = part[len('doubleRotation:'):].strip()
			tokens = [t.strip() for t in tail.split(',') if t.strip()]
			angles = []
			for tok in tokens[:6]:
				try:
					angles.append(convert_angle(tok, 'deg'))
				except Exception:
					angles.append(0.0)
			while len(angles) < 6:
				angles.append(0.0)
			# Two sequential xyz rotations, left-multiplied to match GEMC C++ rotateX/Y/Z calls
			# (g4objectsFactory.cc: rotateX(p0), rotateY(p1), rotateZ(p2), rotateX(p3), ...)
			for axis, ang in zip('xyz', angles[:3]):
				R = _axis_rotation_matrix(axis, ang) @ R
			for axis, ang in zip('xyz', angles[3:]):
				R = _axis_rotation_matrix(axis, ang) @ R
			continue

		order = 'xyz'
		angles_str = part
		if part.startswith('ordered:'):
			tail = part[len('ordered:'):].strip()
			comma_idx = tail.index(',')
			order = tail[:comma_idx].strip()
			angles_str = tail[comma_idx + 1:].strip()

		tokens = [t.strip() for t in angles_str.split(',') if t.strip()]
		angles_deg = []
		for tok in tokens[:3]:
			try:
				angles_deg.append(convert_angle(tok, 'deg'))
			except Exception:
				angles_deg.append(0.0)
		while len(angles_deg) < 3:
			angles_deg.append(0.0)

		# Apply axes in listed order (intrinsic): pre-multiply so each Ri is applied last.
		for i, axis in enumerate(order):
			Ri = _axis_rotation_matrix(axis, angles_deg[i])
			R = Ri @ R

	return R


class GMesh:
	def __init__(
			self,
			name,
			mesh,
			mother=None,
			material=None,
			mfield=None,
			color="white",
			position=(0.0, 0.0, 0.0),
			rotation=(0.0, 0.0, 0.0),
			opacity=1.0,
	):
		"""
		name:       string ID (must be unique so we can look it up in the dict)
		mesh:       pyvista mesh in its own local coordinates
		mother:     string name of parent GMesh, or None
		material:   e.g. "G4_Aluminum"
		mfield:     e.g. "solenoid_field"
		color:      display color
		position:   local translation (x,y,z) relative to mother
		rotation:   local rotation (rx, ry, rz) in degrees, intrinsic ZYX
					i.e. rotate around X, then Y, then Z at this node
		"""
		self.name = name
		self.mesh = mesh
		self.mother = mother
		self.material = material
		self.mfield = mfield
		self.color = color
		self.opacity = float(opacity)

		self.position = np.array(position, dtype=float)
		self.rotation = np.array(rotation, dtype=float)  # (rx, ry, rz) degrees

		# caches
		self._world_position = None  # np.array([x,y,z])
		self._world_rotation = None  # 3x3 np.array

	def compute_world_transform(self, lookup):
		"""
		Returns (R_world, T_world)
		where:
		  R_world is a 3x3 rotation matrix taking *this mesh's local coords*
		  into world coords.
		  T_world is a 3-vector translation in world coords.
		Recursively accumulates parent's transform.
		Caches results.
		"""

		if (self._world_rotation is not None) and (self._world_position is not None):
			return self._world_rotation, self._world_position

		# local rotation and translation of THIS node
		R_local = euler_matrix_zyx(*self.rotation)
		T_local = self.position

		if self.mother is None:
			# root: world = local
			R_world = R_local
			T_world = T_local
		else:
			parent = lookup[self.mother]
			R_parent, T_parent = parent.compute_world_transform(lookup)

			# child world rotation = R_parent * R_local
			R_world = R_parent @ R_local

			# child world translation = T_parent + R_parent * T_local
			# (because child's local offset is expressed in parent's frame,
			#  which may itself be rotated)
			T_world = T_parent + (R_parent @ T_local)

		# cache
		self._world_rotation = R_world
		self._world_position = T_world

		return R_world, T_world

	def world_mesh(self, lookup):
		"""
		Build and return a transformed copy of self.mesh, in world coordinates.
		Applies rotation first, then translation.
		"""
		R_world, T_world = self.compute_world_transform(lookup)

		# copy so we don't mutate original
		world_copy = self.mesh.copy()

		# apply rotation: rotate points around origin using R_world
		pts = world_copy.points.copy()  # (N,3)
		pts = pts @ R_world.T  # apply rotation
		# note: we do pts @ R^T because pts are row vectors

		# apply translation
		pts = pts + T_world

		# update mesh points
		world_copy.points = pts

		return world_copy


def get_center(gvolume) -> tuple:
	raw = gvolume.position
	tokens = [t.strip() for t in raw.split(',') if t.strip()]
	return convert_list(tokens)


def get_dimensions(gvolume) -> tuple:
	raw = gvolume.parameters
	# split strictly on commas and trim; keep ALL tokens
	tokens = [t.strip() for t in raw.split(',') if t.strip()]
	return convert_list(tokens)


def _should_render_pyvista_variation(gconfiguration) -> bool:
	requested = getattr(gconfiguration, 'pyvista_variation', None)
	current = getattr(gconfiguration, 'variation', None)

	if requested:
		return current == requested

	if not hasattr(gconfiguration, '_pyvista_first_variation'):
		gconfiguration._pyvista_first_variation = None

	if gconfiguration._pyvista_first_variation is None:
		gconfiguration._pyvista_first_variation = current

	return current == gconfiguration._pyvista_first_variation


def _pyvista_color_and_metallic(gvolume):
	metallic = False
	pcolor = gvolume.color
	rgb = gvolume.gcolor  # already converted to 'RRGGBB'
	if pcolor != '778899':  # hardcoded from default
		if ',' in pcolor:
			parts = pcolor.split(',')
			if len(parts) == 2:
				if parts[0].lower() == 'metallic':
					metallic = True
				rgb = parts[1]
		else:
			rgb = pcolor
	return rgb, metallic


def _build_volume_mesh(gvolume, gconfiguration):
	pv = gconfiguration.pv

	if gvolume.solid == 'G4Polycone':
		return _add_polycone_from_gvolume(pv, gvolume), ()

	pars = get_dimensions(gvolume)
	if gvolume.solid == 'G4Box':
		return add_box(pv, pars), pars
	if gvolume.solid == 'G4Cons':
		return add_cons(pv, pars), pars
	if gvolume.solid == 'G4Tubs':
		return add_cylinder(pv, pars), pars
	if gvolume.solid == 'G4Trd':
		return add_trapezoid(pv, pars), pars
	if gvolume.solid == 'G4Trap':
		return add_general_trap(pv, pars), pars
	if gvolume.solid == 'G4Sphere':
		return add_sphere(pv, pars), pars
	return None, pars


def _world_transform(gvolume, gconfiguration, t_local):
	# Build F_local: the forward matrix mapping local column vectors to parent column vectors.
	# passive (G4PVPlacement(&R, T)): Geant4 stores frot=R directly, navigation applies
	#   p_local = R @ (p_world - T), so p_world = R^T @ p_local + T → F_local = R^T = R_raw.T
	# active  (G4Transform3D(R, T)): Geant4 inverts the transform, so p_world = R @ p_local + T
	#   → F_local = R_raw
	rotation_str = gvolume.get_rotation_string() if hasattr(gvolume, 'get_rotation_string') else ''
	r_raw = parse_rotation_string(rotation_str)
	placement_type = getattr(gvolume, 'g4placement_type', 'active')
	f_local = r_raw.T if placement_type == 'passive' else r_raw

	if not hasattr(gconfiguration, '_world_transforms'):
		gconfiguration._world_transforms = {}

	mother = getattr(gvolume, 'mother', 'root')
	if mother in (None, 'root', ''):
		f_world, t_world = f_local, t_local
	elif mother in gconfiguration._world_transforms:
		f_parent, t_parent = gconfiguration._world_transforms[mother]
		f_world = f_parent @ f_local
		t_world = t_parent + f_parent @ t_local
	else:
		# Mother not yet rendered (unusual ordering) — use local transform only.
		f_world, t_world = f_local, t_local

	gconfiguration._world_transforms[gvolume.name] = (f_world, t_world)
	return f_world, t_world


def _prepare_volume_render_entry(gvolume, gconfiguration):
	rgb, metallic = _pyvista_color_and_metallic(gvolume)
	alpha = gvolume.opacity
	t_local = np.array(get_center(gvolume), dtype=float)
	mstyle = "surface" if gvolume.style in (1, 2) else "wireframe"
	mlinewidth = 1.0
	if gvolume.visible == 0:
		alpha = 0.05  # nearly invisible
		mstyle = "wireframe"

	mesh, pars = _build_volume_mesh(gvolume, gconfiguration)

	if int(getattr(gconfiguration, 'verbosity', 0) or 0) > 0:
		print(
			f'Volume: {gvolume.name}, Solid: {gvolume.solid}, Center: {t_local}, '
			f'Pars: {pars}, Color: {rgb}, Alpha: {alpha}')

	if mesh is None:
		return None

	f_world, t_world = _world_transform(gvolume, gconfiguration, t_local)

	# Apply world transform: mesh.points are row vectors → pts @ F_world.T + T_world
	# applies F_world to each point as a column vector, then translates.
	world_mesh = mesh.copy()
	world_mesh.points = mesh.points @ f_world.T + t_world

	flat_solids = {'G4Box', 'G4Trd', 'G4Trap'}
	return {
		"mesh": world_mesh,
		"color": rgb,
		"opacity": alpha,
		"style": mstyle,
		"line_width": mlinewidth,
		"smooth_shading": gvolume.solid not in flat_solids,
		"metallic": metallic,
		"volume_style": gvolume.style,
		"visible": gvolume.visible,
		"solid": gvolume.solid,
	}


def _add_detailed_pyvista_entry(gconfiguration, entry):
	if entry["volume_style"] == 2 and entry["visible"] != 0:
		actor = gconfiguration.add_mesh(
			entry["mesh"],
			color=entry["color"],
			smooth_shading=entry["smooth_shading"],
			opacity=min(entry["opacity"], 0.025),
			style="surface",
			line_width=1.0,
		)
		cloud = cloud_points_from_surface(gconfiguration.pv, entry["mesh"])
		cloud_actor = gconfiguration.add_mesh(
			cloud,
			color=entry["color"],
			opacity=min(entry["opacity"], 0.18),
			style="points",
			point_size=4,
			render_points_as_spheres=True,
			lighting=False,
		)
		configure_actor_lighting(cloud_actor, metallic=False)
		configure_actor_lighting(actor, metallic=entry["metallic"])
		return

	if entry["style"] == "wireframe":
		# Render only feature edges so triangulated solids show clean outlines.
		edges = entry["mesh"].extract_feature_edges(
			feature_angle=30,
			boundary_edges=True,
			feature_edges=True,
			manifold_edges=False,
			non_manifold_edges=False,
		)
		actor = gconfiguration.add_mesh(
			edges,
			color=entry["color"],
			opacity=entry["opacity"],
			line_width=entry["line_width"],
		)
	else:
		actor = gconfiguration.add_mesh(
			entry["mesh"],
			color=entry["color"],
			smooth_shading=entry["smooth_shading"],
			opacity=entry["opacity"],
			style=entry["style"],
			line_width=entry["line_width"],
		)
	configure_actor_lighting(actor, metallic=entry["metallic"])


def _combine_pyvista_meshes(pv, meshes):
	if len(meshes) == 1:
		return meshes[0]
	return pv.MultiBlock(meshes).combine(merge_points=False)


def _add_fast_pyvista_entries(gconfiguration, entries):
	batches = {}
	detailed_entries = []
	for entry in entries:
		if entry["volume_style"] == 2 and entry["visible"] != 0:
			detailed_entries.append(entry)
			continue

		key = (
			entry["color"],
			entry["opacity"],
			entry["style"],
			entry["line_width"],
			entry["smooth_shading"],
			entry["metallic"],
			entry["solid"],
		)
		batches.setdefault(key, []).append(entry["mesh"])

	for key, meshes in batches.items():
		color, opacity, style, line_width, smooth_shading, metallic, _solid = key
		mesh = _combine_pyvista_meshes(gconfiguration.pv, meshes)
		actor = gconfiguration.add_mesh(
			mesh,
			color=color,
			smooth_shading=smooth_shading,
			opacity=opacity,
			style=style,
			line_width=line_width,
		)
		configure_actor_lighting(actor, metallic=metallic)

	for entry in detailed_entries:
		_add_detailed_pyvista_entry(gconfiguration, entry)


def flush_pyvista_rendering(gconfiguration):
	if getattr(gconfiguration, '_pyvista_render_entries_flushed', False):
		return

	entries = getattr(gconfiguration, '_pyvista_render_entries', [])
	if not entries:
		gconfiguration._pyvista_render_entries_flushed = True
		return

	fast_setting = getattr(gconfiguration, 'pyvista_fast', None)
	threshold = getattr(gconfiguration, 'pyvista_fast_threshold', 1000)
	use_fast = fast_setting is True or (fast_setting is None and len(entries) > threshold)

	if use_fast:
		_add_fast_pyvista_entries(gconfiguration, entries)
	else:
		for entry in entries:
			_add_detailed_pyvista_entry(gconfiguration, entry)

	gconfiguration._pyvista_render_entries = []
	gconfiguration._pyvista_render_entries_flushed = True


def render_volume(gvolume, gconfiguration):
	if gconfiguration.use_pyvista:
		if not _should_render_pyvista_variation(gconfiguration):
			return

		entry = _prepare_volume_render_entry(gvolume, gconfiguration)
		if entry is None:
			return

		if not hasattr(gconfiguration, '_pyvista_render_entries'):
			gconfiguration._pyvista_render_entries = []
		gconfiguration._pyvista_render_entries.append(entry)
		gconfiguration._pyvista_render_entries_flushed = False


def configure_actor_lighting(actor, metallic=False):
	if actor is None:
		return

	actor.prop.ambient = 0.25
	actor.prop.diffuse = 0.75

	if not metallic:
		actor.prop.specular = 0.0
		return

	actor.prop.specular = 0.15
	try:
		actor.prop.interpolation = "pbr"
		actor.prop.metallic = 0.4
		actor.prop.roughness = 0.4
	except Exception:
		pass


def cloud_points_from_surface(pv, mesh, n_points=8000):
	"""Create a deterministic PyVista point cloud sampled from a mesh surface."""
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			surface = mesh.extract_surface(algorithm="dataset_surface").triangulate()
	except Exception:
		return mesh

	try:
		points = np.asarray(surface.points)
		faces = np.asarray(surface.faces).reshape((-1, 4))[:, 1:4]
		triangles = points[faces]
		areas = 0.5 * np.linalg.norm(
			np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]),
			axis=1,
		)
		total_area = areas.sum()
		if total_area <= 0:
			return pv.PolyData(points)

		rng = np.random.default_rng(12345)
		triangle_ids = rng.choice(len(triangles), size=n_points, p=areas / total_area)
		selected = triangles[triangle_ids]

		u = rng.random(n_points)
		v = rng.random(n_points)
		flip = (u + v) > 1.0
		u[flip] = 1.0 - u[flip]
		v[flip] = 1.0 - v[flip]

		sampled = (
			selected[:, 0]
			+ u[:, None] * (selected[:, 1] - selected[:, 0])
			+ v[:, None] * (selected[:, 2] - selected[:, 0])
		)

		bounds = np.array(mesh.bounds, dtype=float)
		scene_scale = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4], 1.0)
		sampled += rng.normal(scale=0.003 * scene_scale, size=sampled.shape)
		return pv.PolyData(sampled)
	except Exception:
		return pv.PolyData(surface.points)


def move_to_center(mesh, target_center):
	"""Translate mesh so its center becomes target_center."""
	target = np.asarray(target_center, dtype=float)
	curr = np.asarray(mesh.center, dtype=float)
	delta = target - curr
	out = mesh.copy()
	out.translate(tuple(delta), inplace=True)
	return out


def add_box(pv, pars) -> None:
	volume = pv.Cube(
		x_length=pars[0] * 2, y_length=pars[1] * 2, z_length=pars[2] * 2
	)
	return volume


def add_cylinder(pv, pars):
	"""
	pars = (rmin, rmax, hz, phi_start_deg, dphi_deg)
	Builds a watertight G4Tubs without boolean ops.
	"""
	rmin, rmax, hz, phi_start, dphi = map(float, pars)
	if rmax <= 0 or hz <= 0:
		raise ValueError(f"Invalid cylinder sizes: rmax={rmax}, hz={hz}")

	# angular resolution: denser for small sectors
	res = max(32, int(256 * (dphi / 360.0 if dphi < 360.0 else 1.0)))

	def polydata_from_pts_faces(pts, faces_idx):
		poly = pv.PolyData()
		poly.points = np.array(pts, dtype=float)
		# faces_idx like [n, i0,i1,..., in-1]
		poly.faces = np.array(faces_idx, dtype=np.int64)
		return poly

	if rmin <= 0.0:
		# SOLID cylinder: include the axis so the revolution fills the volume
		# Quad in X–Z plane (Y=0): (rmax,-hz)->(rmax,+hz)->(0,+hz)->(0,-hz)
		pts = [
			[rmax, 0.0, -hz],
			[rmax, 0.0, +hz],
			[0.0, 0.0, +hz],
			[0.0, 0.0, -hz],
		]
		faces = [4, 0, 1, 2, 3]  # one quad
		profile = polydata_from_pts_faces(pts, faces)
	else:
		# HOLLOW tube: a rectangular ring in (r,z): (rmin,-hz)->(rmax,-hz)->(rmax,+hz)->(rmin,+hz)
		# This revolved surface is closed in 360° and remains watertight for partial φ with capping
		pts = [
			[rmin, 0.0, -hz],  # 0
			[rmax, 0.0, -hz],  # 1
			[rmax, 0.0, +hz],  # 2
			[rmin, 0.0, +hz],  # 3
		]
		faces = [4, 0, 1, 2, 3]
		profile = polydata_from_pts_faces(pts, faces)

	# Revolve only the requested angle; capping=True closes ends (and radial faces for φ<360)
	tube = profile.extrude_rotate(angle=dphi, resolution=res, capping=True)

	# Align φ start
	if dphi < 360.0 or abs(phi_start) > 1e-12:
		tube = tube.rotate_z(phi_start, inplace=False)

	return tube.triangulate().clean()


def add_cons(pv, pars):
	"""
	Build a G4Cons-like solid.

	Parameters (numerical; already in your scene units):
	  pars[0] = rin1     # inner radius at z = -length
	  pars[1] = rout1    # outer radius at z = -length
	  pars[2] = rin2     # inner radius at z = +length
	  pars[3] = rout2    # outer radius at z = +length
	  pars[4] = length   # HALF length in z (i.e., dz)
	  pars[5] = phi_start (degrees)
	  pars[6] = phi_total (degrees)

	bcenter: (x, y, z) center in world coords.

	Returns: closed PolyData surface suitable for rendering/CSG.
	"""
	# --- unpack
	rin1 = pars[0]
	rout1 = pars[1]
	rin2 = pars[2]
	rout2 = pars[3]
	hz = pars[4]
	phi_start = pars[5]
	phi_total = pars[6]

	res = 128  # resolution

	def solid_to_axis(r0, z0, r1, z1):
		"""Make a quad polygon in X–Z plane (Y=0) that includes the axis."""
		pts = np.array([
			[r0, 0.0, z0],  # outer @ z0
			[r1, 0.0, z1],  # outer @ z1
			[0.0, 0.0, z1],  # axis @ z1
			[0.0, 0.0, z0],  # axis @ z0
		], dtype=float)
		poly = pv.PolyData()
		poly.points = pts
		# one polygon with 4 verts: [n, i0, i1, i2, i3]
		poly.faces = np.array([4, 0, 1, 2, 3], dtype=np.int64)
		return poly

	# Build a solid outer frustum-to-axis and revolve only phi_total
	outer_profile = solid_to_axis(rout1, -hz, rout2, +hz)
	outer = outer_profile.extrude_rotate(angle=phi_total, resolution=res, capping=True)

	# If inner radii present, build inner solid-to-axis and subtract
	have_inner = (rin1 > 0.0) or (rin2 > 0.0)
	if have_inner:
		inner_profile = solid_to_axis(rin1, -hz, rin2, +hz)
		inner = inner_profile.extrude_rotate(angle=phi_total, resolution=res, capping=True)
		cons = outer.triangulate().clean().boolean_difference(inner.triangulate().clean())
	else:
		cons = outer

	# Rotate sector start and translate to center
	if phi_total < 360.0 or abs(phi_start) > 1e-12:
		cons = cons.rotate_z(phi_start, inplace=False)

	# Final tidy
	cons = cons.triangulate().clean()

	return cons


def add_trapezoid(pv, pars) -> None:
	"""
	Build a G4Trd in PyVista.

	Geant4 parameter order (half-lengths):
	  pars[0] = dx1  # half-length X at z = -dz
	  pars[1] = dx2  # half-length X at z = +dz
	  pars[2] = dy1  # half-length Y at z = -dz
	  pars[3] = dy2  # half-length Y at z = +dz
	  pars[4] = dz   # half-length in Z

	bcenter: (x,y,z) where the solid’s local origin (0,0,0) should land.
	Returns: closed PolyData.
	"""
	dx1, dx2, dy1, dy2, dz = map(float, pars[:5])

	# 	dx1 *= 0.5;
	# 	dx2 *= 0.5;
	# 	dy1 *= 0.5;
	# 	dy2 *= 0.5;
	# 	dz *= 0.5

	z0, z1 = -dz, +dz

	# Eight vertices: bottom (-z) then top (+z)
	# Order each face CCW when viewed from outside.
	pts = np.array([
		[-dx1, -dy1, z0],  # 0 bottom
		[+dx1, -dy1, z0],  # 1
		[+dx1, +dy1, z0],  # 2
		[-dx1, +dy1, z0],  # 3
		[-dx2, -dy2, z1],  # 4 top
		[+dx2, -dy2, z1],  # 5
		[+dx2, +dy2, z1],  # 6
		[-dx2, +dy2, z1],  # 7
	], dtype=float)

	# Six quad faces (bottom, top, and 4 sides)
	faces = np.array([
		4, 0, 1, 2, 3,  # bottom (-z)
		4, 4, 5, 6, 7,  # top (+z)
		4, 0, 1, 5, 4,  # -Y side
		4, 1, 2, 6, 5,  # +X side
		4, 2, 3, 7, 6,  # +Y side
		4, 3, 0, 4, 7,  # -X side
	], dtype=np.int64)

	trd = pv.PolyData(pts, faces)
	# (Optional) robustness: ensure triangulated & watertight
	trd = trd.triangulate().clean()

	return trd


def add_general_trap(pv, pars):
	"""Build a G4Trap solid with 11 parameters (general trapezoid).

	pars (mm / deg, as returned by get_dimensions with auto-unit detection):
	  [0]  pDz     half-length in z  (mm)
	  [1]  pTheta  polar angle of line joining face centres  (deg)
	  [2]  pPhi    azimuthal angle of that line  (deg)
	  [3]  pDy1    half Y at z = -pDz  (mm)
	  [4]  pDx1    half X at y = -pDy1 on the -z face  (mm)
	  [5]  pDx2    half X at y = +pDy1 on the -z face  (mm)
	  [6]  pAlp1   tilt of -z face from Y axis  (deg)
	  [7]  pDy2    half Y at z = +pDz  (mm)
	  [8]  pDx3    half X at y = -pDy2 on the +z face  (mm)
	  [9]  pDx4    half X at y = +pDy2 on the +z face  (mm)
	  [10] pAlp2   tilt of +z face from Y axis  (deg)

	Vertex layout matches Geant4's G4Trap::CreateRotatedVertices ordering.
	"""
	pDz  = float(pars[0])
	tc   = np.tan(np.deg2rad(float(pars[1]))) * np.cos(np.deg2rad(float(pars[2])))
	ts   = np.tan(np.deg2rad(float(pars[1]))) * np.sin(np.deg2rad(float(pars[2])))
	pDy1 = float(pars[3])
	pDx1 = float(pars[4])
	pDx2 = float(pars[5])
	ta1  = np.tan(np.deg2rad(float(pars[6])))
	pDy2 = float(pars[7])
	pDx3 = float(pars[8])
	pDx4 = float(pars[9])
	ta2  = np.tan(np.deg2rad(float(pars[10])))

	pts = np.array([
		[-pDz*tc - pDy1*ta1 - pDx1, -pDz*ts - pDy1, -pDz],  # v0
		[-pDz*tc - pDy1*ta1 + pDx1, -pDz*ts - pDy1, -pDz],  # v1
		[-pDz*tc + pDy1*ta1 + pDx2, -pDz*ts + pDy1, -pDz],  # v2
		[-pDz*tc + pDy1*ta1 - pDx2, -pDz*ts + pDy1, -pDz],  # v3
		[+pDz*tc - pDy2*ta2 - pDx3, +pDz*ts - pDy2, +pDz],  # v4
		[+pDz*tc - pDy2*ta2 + pDx3, +pDz*ts - pDy2, +pDz],  # v5
		[+pDz*tc + pDy2*ta2 + pDx4, +pDz*ts + pDy2, +pDz],  # v6
		[+pDz*tc + pDy2*ta2 - pDx4, +pDz*ts + pDy2, +pDz],  # v7
	], dtype=float)

	faces = np.array([
		4, 0, 3, 2, 1,  # -z face
		4, 4, 5, 6, 7,  # +z face
		4, 0, 1, 5, 4,  # -y side
		4, 1, 2, 6, 5,  # +x side
		4, 2, 3, 7, 6,  # +y side
		4, 3, 0, 4, 7,  # -x side
	], dtype=np.int64)

	trap = pv.PolyData(pts, faces)
	return trap.triangulate().clean()


def add_sphere(pv, pars):
	"""Build a G4Sphere solid (spherical shell section).

	pars (deg / mm from get_dimensions):
	  [0] rmin    inner radius (mm); 0 for solid sphere
	  [1] rmax    outer radius (mm)
	  [2] sphi    start azimuthal angle (deg)
	  [3] dphi    delta azimuthal angle (deg)
	  [4] stheta  start polar angle from +z (deg)
	  [5] dtheta  delta polar angle (deg)

	Builds a 2-D cross-section in the XZ plane and revolves it by dphi.
	The cross-section arc traces the sphere surface so the result is always
	watertight — avoiding VTK boolean ops on partial (non-closed) shells.
	"""
	rmin   = float(pars[0])
	rmax   = float(pars[1])
	sphi   = float(pars[2])
	dphi   = float(pars[3])
	stheta = float(pars[4])
	dtheta = float(pars[5])

	N = 48
	theta_s = np.deg2rad(stheta)
	theta_e = np.deg2rad(stheta + dtheta)
	thetas  = np.linspace(theta_s, theta_e, N)

	# Outer arc in XZ plane (y=0): x = r*sin(θ)  (cylindrical radius), z = r*cos(θ)
	outer = np.column_stack([rmax * np.sin(thetas), np.zeros(N), rmax * np.cos(thetas)])

	if rmin > 0.0:
		inner = np.column_stack([rmin * np.sin(thetas[::-1]), np.zeros(N), rmin * np.cos(thetas[::-1])])
		profile_pts = np.vstack([outer, inner])
	else:
		# Solid sector: close through the origin
		profile_pts = np.vstack([outer, [[0.0, 0.0, 0.0]]])

	npts = len(profile_pts)
	poly = pv.PolyData()
	poly.points = profile_pts.astype(float)
	poly.faces  = np.array([npts] + list(range(npts)), dtype=np.int64)

	shell = poly.extrude_rotate(angle=dphi, resolution=96, capping=True)
	if abs(sphi) > 1e-6:
		shell = shell.rotate_z(sphi, inplace=False)
	result = shell.triangulate().clean()
	# split_sharp_edges gives crisp edges at the phi/theta cuts while keeping spherical surfaces smooth
	result.compute_normals(split_vertices=True, feature_angle=30, inplace=True)
	return result


def add_polycone(pv, phi_start, phi_total, zplane, iradius, oradius):
	"""Build a G4Polycone solid by revolving a closed 2-D cross-section profile.

	Outer boundary (forward) + inner boundary (reversed, or z-axis when rin=0) form
	a single closed polygon that, when revolved, produces the hollow solid without
	needing boolean operations.
	"""
	n = len(zplane)
	res = 128

	outer_pts = [[oradius[i], 0.0, zplane[i]] for i in range(n)]
	have_inner = any(r > 0.0 for r in iradius)
	if have_inner:
		inner_pts = [[iradius[i], 0.0, zplane[i]] for i in range(n - 1, -1, -1)]
	else:
		inner_pts = [[0.0, 0.0, zplane[i]] for i in range(n - 1, -1, -1)]

	profile_pts = np.array(outer_pts + inner_pts, dtype=float)
	npts = len(profile_pts)
	poly = pv.PolyData()
	poly.points = profile_pts
	poly.faces = np.array([npts] + list(range(npts)), dtype=np.int64)

	result = poly.extrude_rotate(angle=phi_total, resolution=res, capping=True)
	if abs(phi_start) > 1e-6:
		result = result.rotate_z(phi_start, inplace=False)
	result = result.triangulate().clean()
	result.compute_normals(split_vertices=True, feature_angle=30, inplace=True)
	return result


def _add_polycone_from_gvolume(pv, gvolume):
	"""Parse G4Polycone parameters (which include a unit-less nplanes token) and call add_polycone."""
	from .g4_units import convert_angle, convert_length
	tokens = [t.strip() for t in gvolume.parameters.split(',') if t.strip()]
	if len(tokens) < 3:
		return None
	phi_start = convert_angle(tokens[0], 'deg')
	phi_total = convert_angle(tokens[1], 'deg')
	nplanes = int(tokens[2])
	if len(tokens) < 3 + 3 * nplanes:
		return None
	rest = tokens[3:]

	def to_mm(tok):
		return convert_length(tok, 'mm')

	zplane  = [to_mm(rest[i])              for i in range(nplanes)]
	iradius = [to_mm(rest[nplanes + i])    for i in range(nplanes)]
	oradius = [to_mm(rest[2 * nplanes + i]) for i in range(nplanes)]
	return add_polycone(pv, phi_start, phi_total, zplane, iradius, oradius)


def _is_box_like(mesh):
	"""
	Heuristic for pv.Cube():
	- PolyData
	- typically 8 points, axis-aligned bounds
	"""
	import pyvista as pv
	if not isinstance(mesh, pv.PolyData):
		return False
	# pv.Cube usually has 8 points. We keep it simple.
	return mesh.n_points == 8


def _is_cylinder_like(mesh):
	"""
	Heuristic for pv.Cylinder():
	- PolyData
	- many points (circular cross-section tessellated)
	- XY extents ~same
	"""
	import pyvista as pv
	if not isinstance(mesh, pv.PolyData):
		return False
	if mesh.n_points < 20:
		return False

	xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
	rx = 0.5 * (xmax - xmin)
	ry = 0.5 * (ymax - ymin)
	if rx == 0:
		return False
	ratio = ry / rx
	return 0.8 <= ratio <= 1.25  # "round-ish" in xy


def _is_sphere_like(mesh):
	"""
	Heuristic for pv.Sphere():
	- PolyData
	- many points
	- extents in x,y,z similar
	"""
	import pyvista as pv
	if not isinstance(mesh, pv.PolyData):
		return False
	if mesh.n_points < 30:
		return False

	xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds
	dx = xmax - xmin
	dy = ymax - ymin
	dz = zmax - zmin
	if dx == 0 or dy == 0:
		return False
	xy_ratio = dy / dx
	yz_ratio = dz / dy if dy != 0 else 0.0

	return (0.8 <= xy_ratio <= 1.25) and (0.8 <= yz_ratio <= 1.25)


def gmesh_to_geant4_solid_and_params(gm, length_unit='mm', angle_unit='deg'):
	"""
	Given a GMesh (which holds gm.mesh: a PyVista mesh),
	return (solid_name, parameters_string) suitable for GVolume.

	Supported so far:
	  - pv.Cube      -> G4Box
	  - pv.Cylinder  -> G4Tubs  (full 360°, solid)
	  - pv.Sphere    -> G4Sphere (full sphere)
	"""

	mesh = gm.mesh
	xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds

	# Box (pv.Cube -> G4Box)
	if _is_box_like(mesh):
		# Geant4 G4Box takes HALF-lengths along x,y,z
		px = 0.5 * (xmax - xmin)
		py = 0.5 * (ymax - ymin)
		pz = 0.5 * (zmax - zmin)

		param_string = f"{px}*{length_unit}, {py}*{length_unit}, {pz}*{length_unit}"
		return "G4Box", param_string

	# Sphere must be checked before cylinder: a sphere also passes _is_cylinder_like
	# (both are "round in XY") so we disambiguate first by requiring all three extents equal.
	if _is_sphere_like(mesh):
		rx = 0.5 * (xmax - xmin)
		ry = 0.5 * (ymax - ymin)
		rz = 0.5 * (zmax - zmin)
		rmax = (rx + ry + rz) / 3.0  # average radius
		rmin = 0.0

		sphi = 0.0
		dphi = 360.0
		stheta = 0.0
		dtheta = 180.0

		param_string = (
			f"{rmin}*{length_unit}, "
			f"{rmax}*{length_unit}, "
			f"{sphi}*{angle_unit}, "
			f"{dphi}*{angle_unit}, "
			f"{stheta}*{angle_unit}, "
			f"{dtheta}*{angle_unit}"
		)
		return "G4Sphere", param_string

	# Cylinder (pv.Cylinder -> G4Tubs)
	# height along Z, radius in XY.
	if _is_cylinder_like(mesh):
		rmax = 0.5 * ((xmax - xmin) + (ymax - ymin)) / 2.0
		rmin = 0.0
		half_z = 0.5 * (zmax - zmin)
		sphi = 0.0
		dphi = 360.0
		param_string = (
			f"{rmin}*{length_unit}, "
			f"{rmax}*{length_unit}, "
			f"{half_z}*{length_unit}, "
			f"{sphi}*{angle_unit}, "
			f"{dphi}*{angle_unit}"
		)
		return "G4Tubs", param_string

	# Not recognized yet (cones/polycones/etc.)
	return None, None


def pvmeshes_from_gmeshes(gmeshes):
	# build lookup dict for hierarchy resolution
	shape_dict = {gm.name: gm for gm in gmeshes}

	pymeshes = []

	# add world-space meshes
	for gm in gmeshes:
		world_poly = gm.world_mesh(shape_dict)
		pymeshes.append(
			(world_poly, gm.color, gm.opacity)
		)

	return pymeshes


def set_yz_view_x_into_screen(p, distance=10.0):
	"""
	Arrange the camera so:
	  - +Z points to the right on screen
	  - +X points into the screen (depth)
	  - We're looking along -X toward the origin

	Note:
	  This choice forces screen-up to be world -Y.
	  In other words, +Y will appear downward.
	"""
	eye = (-distance, 0.0, 0.0)  # camera sitting on -X
	focus = (0.0, 0.0, 0.0)  # look at origin -> looking along -X
	view_up = (0.0, 1.0, 0.0)  # flipped so Z is to the right

	p.camera_position = [eye, focus, view_up]
