#!/usr/bin/env python3

# Purpose:
#   Upload CAD volume definitions from a single human-authored file (YAML or JSON) into the
#   SQLite `geometry` table, so that GEMC3's SQLite factory loads them like any other volume.
#
#   This is the modern replacement for the clas12Tags Perl mechanism (GXML.pm / cad.pm /
#   gxml_to_sqlite.pl) that parsed a `cad_<variation>.gxml` file into a dedicated `cad` table.
#   Here there is no dedicated table: each entry becomes a normal GVolume with solid="CAD" and
#   the STL path carried in the `description` column (see GSystem::addVolumeFromFile in ../src and
#   the CAD g4 builder, which reads the mesh path from `description`).
#
#   Authoritative-list semantics: ONLY volumes with an entry in the file are written to the
#   database. STL files that are present on disk but absent from the file are never uploaded and
#   therefore never loaded by GEMC3.
#
# File format (YAML shown; JSON with the same keys is also accepted):
#
#   system:     htcc            # required. The GEMC system name (row key).
#   experiment: clas12          # optional. Defaults to --experiment, else to `system`.
#   variation:  default         # optional. Defaults to 'default'.
#   run:        1               # optional. Defaults to 1.
#   cad_dir:    cad             # optional. Runtime subdirectory holding the meshes. Default 'cad'.
#   extension:  stl             # optional. Mesh file extension. Default 'stl'.
#   defaults:                   # optional. Applied to every volume, overridden per volume.
#     material: rohacell31
#     color:    "888888"
#   volumes:                    # required. One entry per CAD piece; `name` matches the mesh stem.
#     - name: htccMollerConeExt
#       position: 0*cm, 0*cm, 0.1*cm
#       rotation: 0*deg, 180*deg, 0*deg
#       scale:    10            # optional uniform mesh scale (default 1). e.g. a mesh drawn in
#                              # cm uses scale 10; the CAD builder multiplies the mm interpretation.
#     - name: htccCone
#       sensitivity: flux       # alias for `digitization`
#       identifier: "id: 3"     # alias `identifiers` also accepted

# python
import json
import os
import sys
import types

# gemc api
from .gutils import GColors

# Keys accepted in a volume (or defaults) entry, mapped to their GVolume attribute.
# Aliases keep the familiar clas12/gxml vocabulary while writing modern GVolume columns.
_FIELD_MAP = {
	'material': 'material',
	'mother': 'mother',
	'position': 'position',
	'color': 'color',
	'visible': 'visible',
	'style': 'style',
	'opacity': 'opacity',
	'mfield': 'mfield',
	'g4placement_type': 'g4placement_type',
	'digitization': 'digitization',
	'sensitivity': 'digitization',   # gxml alias
	'identifier': 'identifier',
	'identifiers': 'identifier',      # gxml alias
	'description': 'description',
	'exist': 'exist',
	'exists': 'exist',                # convenience alias
}


# --------------------------------------------------------------------------------------------------
# File loading (YAML or JSON)
# --------------------------------------------------------------------------------------------------

def load_cad_document(filename):
	"""Return the CAD definition file as a Python dict.

	JSON is parsed with the standard library. YAML is parsed with PyYAML when it is installed;
	otherwise a small block parser handles the restricted document shape documented at the top of
	this module (top-level scalars, one `defaults:` mapping, one `volumes:` sequence of mappings).
	"""
	try:
		with open(filename, encoding='utf-8') as stream:
			text = stream.read()
	except OSError as e:
		sys.exit(f"{GColors.RED}Error reading CAD file {filename}: {e}{GColors.END}")

	is_json = filename.lower().endswith('.json') or text.lstrip().startswith('{')
	if is_json:
		try:
			return json.loads(text)
		except json.JSONDecodeError as e:
			sys.exit(f"{GColors.RED}Error parsing JSON file {filename}: {e}{GColors.END}")

	try:
		import yaml  # PyYAML, optional
		return yaml.safe_load(text)
	except ImportError:
		return _parse_cad_yaml(text)


def _strip_inline_comment(line):
	quote = None
	for i, char in enumerate(line):
		if char in ("'", '"') and (i == 0 or line[i - 1] != '\\'):
			if quote is None:
				quote = char
			elif quote == char:
				quote = None
		elif char == '#' and quote is None:
			return line[:i]
	return line


def _parse_scalar(value):
	value = value.strip()
	if not value:
		return ''
	if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
		return value[1:-1]
	low = value.lower()
	if low == 'true':
		return True
	if low == 'false':
		return False
	if low in ('null', 'none', '~'):
		return None
	try:
		return int(value)
	except ValueError:
		pass
	try:
		return float(value)
	except ValueError:
		return value


def _indent_of(line):
	return len(line) - len(line.lstrip(' '))


def _parse_cad_yaml(text):
	"""Minimal block-YAML parser for the CAD document shape (no PyYAML dependency)."""
	lines = [
		stripped
		for stripped in (_strip_inline_comment(raw.rstrip()) for raw in text.splitlines())
		if stripped.strip()
	]

	doc = {}
	i, n = 0, len(lines)
	while i < n:
		line = lines[i]
		indent = _indent_of(line)
		key, _, value = line.strip().partition(':')
		key = key.strip()
		value = value.strip()

		if value:
			doc[key] = _parse_scalar(value)
			i += 1
			continue

		# Collect the indented child block belonging to this key.
		child = []
		j = i + 1
		while j < n and _indent_of(lines[j]) > indent:
			child.append(lines[j])
			j += 1
		doc[key] = _parse_block(child)
		i = j

	return doc


def _parse_block(lines):
	if not lines:
		return {}
	if lines[0].strip().startswith('- '):
		return _parse_sequence(lines)
	return _parse_mapping(lines)


def _parse_mapping(lines):
	mapping = {}
	for line in lines:
		key, _, value = line.strip().partition(':')
		mapping[key.strip()] = _parse_scalar(value)
	return mapping


def _parse_sequence(lines):
	base = _indent_of(lines[0])
	items = []
	current = None
	for line in lines:
		indent = _indent_of(line)
		stripped = line.strip()
		if indent == base and stripped.startswith('- '):
			if current is not None:
				items.append(current)
			content = stripped[2:].strip()
			key, sep, value = content.partition(':')
			if sep:
				current = {key.strip(): _parse_scalar(value)}
			else:
				current = _parse_scalar(content)
		elif isinstance(current, dict):
			key, sep, value = stripped.partition(':')
			if sep:
				current[key.strip()] = _parse_scalar(value)
	if current is not None:
		items.append(current)
	return items


# --------------------------------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------------------------------

def upload_cad_definitions(cad_file, dbhost, experiment=None, variation=None, run=None, verbosity=1):
	"""Parse a CAD definition file and write one geometry row per listed volume into `dbhost`.

	Only volumes present in the file are uploaded (authoritative list). Existing rows for the same
	(experiment, system, variation, run) are cleared first, matching the SQLite publish semantics.
	"""
	import sqlite3
	from .gvolume import GVolume
	from .gsqlite import create_sqlite_database

	doc = load_cad_document(cad_file)
	if not isinstance(doc, dict):
		sys.exit(f"{GColors.RED}Error: CAD file {cad_file} did not parse into a mapping.{GColors.END}")

	system = doc.get('system')
	if not system:
		sys.exit(f"{GColors.RED}Error: CAD file {cad_file} is missing the required 'system' key.{GColors.END}")

	experiment = experiment or doc.get('experiment') or system
	variation = variation or doc.get('variation') or 'default'
	run = run if run is not None else doc.get('run', 1)
	cad_dir = doc.get('cad_dir', 'cad')
	extension = str(doc.get('extension', 'stl')).lstrip('.')
	defaults = doc.get('defaults') or {}
	volumes = doc.get('volumes') or []

	if not volumes:
		sys.exit(f"{GColors.RED}Error: CAD file {cad_file} lists no volumes.{GColors.END}")

	cfg = _upload_configuration(dbhost, experiment, system, variation, run, sqlite3,
	                            create_sqlite_database)

	file_dir = os.path.dirname(os.path.abspath(cad_file))

	print(f"  {GColors.BOLD}CAD upload{GColors.END} from {cad_file}")
	print(f"    experiment: {experiment}, system: {system}, variation: {variation}, run: {run}")

	for entry in volumes:
		if not isinstance(entry, dict) or 'name' not in entry:
			sys.exit(f"{GColors.RED}Error: every volume entry needs a 'name' (got {entry!r}).{GColors.END}")
		gvolume = _build_gvolume(GVolume, entry, defaults, cad_dir, extension, file_dir)
		gvolume.publish(cfg)
		if verbosity > 0:
			print(f"    + {gvolume.name:<24} -> {gvolume.description}")

	cfg.sqlitedb.commit()
	print(f"  {GColors.GREEN}Uploaded {cfg.nvolumes} CAD volume(s){GColors.END} into {dbhost}")
	if getattr(cfg, 'use_pyvista', False):
		cfg.show()
	cfg.sqlitedb.close()


def _upload_configuration(dbhost, experiment, system, variation, run, sqlite3, create_sqlite_database):
	from .gconfiguration import GConfiguration, get_arguments

	args = get_arguments()
	args.factory = 'sqlite'
	args.dbhost = dbhost
	args.variation = variation
	args.run = run
	wants_pyvista = args.pyvista or args.pyvista_background or bool(args.pyvista_vtksz)

	if wants_pyvista:
		return GConfiguration(experiment, system, args=args)

	is_new = not os.path.exists(dbhost)
	conn = sqlite3.connect(dbhost)
	if is_new:
		create_sqlite_database(conn)

	return types.SimpleNamespace(
		factory='sqlite',
		experiment=experiment,
		system=system,
		variation=variation,
		runno=run,
		sqlitedb=conn,
		nvolumes=0,
		use_pyvista=False,
	)


def _build_gvolume(GVolume, entry, defaults, cad_dir, extension, file_dir):
	# defaults first, then per-volume keys override.
	merged = dict(defaults)
	merged.update(entry)

	name = str(merged.pop('name'))
	gvolume = GVolume(name)

	# Mark as a CAD import. The g4 CAD builder reads the mesh path from `description` and reuses
	# the otherwise-unused `parameters` column to carry the optional uniform `scale` factor
	# (default sentinel 'NULL' -> scale 1.0). 'NULL' also satisfies GVolume.check_validity.
	gvolume.solid = 'CAD'
	scale = merged.pop('scale', None)
	gvolume.parameters = 'NULL' if scale is None else str(scale)

	filename = merged.pop('file', f"{name}.{extension}")
	# Runtime path, resolved by GEMC relative to the system directory (e.g. "cad/htccCone.stl").
	description = os.path.join(cad_dir, filename)

	# Warn (do not fail) when the mesh is not found next to the definition file: the database may
	# be built on a different machine than the one that runs GEMC.
	local_mesh = os.path.join(file_dir, filename)
	if not os.path.exists(local_mesh):
		print(f"  {GColors.YELLOW}Warning:{GColors.END} mesh not found next to definition file: {local_mesh}")

	rotation = merged.pop('rotation', None)
	if rotation is not None:
		gvolume.rotations = [str(rotation)]

	for key, value in merged.items():
		attr = _FIELD_MAP.get(key)
		if attr is None:
			sys.exit(f"{GColors.RED}Error: unknown CAD key '{key}' for volume '{name}'.{GColors.END}")
		setattr(gvolume, attr, value)

	# `description` doubles as the mesh path; an explicit `description` override wins.
	if 'description' not in merged:
		gvolume.description = description

	if gvolume.material is None:
		gvolume.material = 'G4_AIR'

	return gvolume
