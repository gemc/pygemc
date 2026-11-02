#!/usr/bin/env python3

# Purpose:
#   Publish CAD placements through a configuration, or upload definitions from YAML or JSON into the
#   SQLite `geometry` table, so that GEMC3's SQLite factory loads them like any other volume.
#
#   This is the modern replacement for the clas12Tags Perl mechanism (GXML.pm / cad.pm /
#   gxml_to_sqlite.pl) that parsed a `cad_<variation>.gxml` file into a dedicated `cad` table.
#   Here there is no dedicated table: each entry becomes a normal GVolume with solid="CAD" and
#   `parameters: <mesh path>, <scale>`. The `description` column remains available for descriptive
#   text.
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
#       description: External Moller cone
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
import xml.etree.ElementTree as ET

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
	'mirror': 'mirror',              # optical-surface name (loaded by the CAD factory)
	'description': 'description',
	'exist': 'exist',
	'exists': 'exist',                # convenience alias
}


# --------------------------------------------------------------------------------------------------
# File loading (GXML, YAML or JSON)
# --------------------------------------------------------------------------------------------------

def load_cad_document(filename):
	"""Return a GXML, YAML or JSON CAD definition as a Python dict.

	JSON is parsed with the standard library. YAML is parsed with PyYAML when it is installed;
	otherwise a small block parser handles the restricted document shape documented at the top of
	this module (top-level scalars, one `defaults:` mapping, one `volumes:` sequence of mappings).
	"""
	filename = os.fspath(filename)
	try:
		with open(filename, encoding='utf-8') as stream:
			text = stream.read()
	except OSError as e:
		sys.exit(f"{GColors.RED}Error reading CAD file {filename}: {e}{GColors.END}")

	if filename.lower().endswith(('.gxml', '.xml')):
		return _parse_cad_gxml(text)

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


def _parse_cad_gxml(text):
	"""Translate GEMC2 placement attributes to the CAD document vocabulary."""
	volumes = []
	for element in ET.fromstring(text).findall('volume'):
		entry = dict(element.attrib)
		# hitType labels the GEMC2 bank; sensitivity selects readout or an optical skin.
		entry.pop('hitType', None)
		sensitivity = entry.get('sensitivity', '')
		if sensitivity.startswith('mirror:'):
			entry['mirror'] = sensitivity.partition(':')[2].strip()
			entry.pop('sensitivity')
			# Optical labels are not readout identifiers.
			entry.pop('identifiers', None)
			entry.pop('identifier', None)
		for field in ('position', 'rotation'):
			if field in entry:
				value = entry[field]
				prefix = ''
				if field == 'rotation' and value.startswith(('ordered:', 'doubleRotation:')):
					prefix, _, value = value.partition(':')
					prefix += ': '
				entry[field] = prefix + ', '.join(value.replace(',', ' ').split())
		if 'color' in entry:
			entry['color'] = entry['color'].lower()
		for field in ('visible', 'style', 'exist', 'exists'):
			if field in entry:
				entry[field] = int(entry[field])
		if 'opacity' in entry:
			entry['opacity'] = float(entry['opacity'])
		volumes.append(entry)
	return {'defaults': {'rotation': '0*deg, 0*deg, 0*deg'}, 'volumes': volumes}


def build_cad(configuration, source, *, cad_dir=None, defaults=None, material_aliases=None,
			passive=False, warn_missing_meshes=False):
	"""Publish CAD placements through an existing configuration and return their GVolumes.

	source accepts a GXML/YAML/JSON path, a CAD document mapping, or an iterable of volume
	mappings. Only listed placements are published. File metadata never changes configuration's
	experiment, system, variation, run, or output factory, and existing banks are not cleared.

	cad_dir overrides the document's runtime mesh directory (otherwise 'cad'); extension and
	per-volume file/scale keys describe source meshes. copyOf rows reuse a source solid.
	defaults override document defaults, while individual entries take precedence over both.
	material_aliases maps source material names to their runtime equivalents.

	passive=True forces GEMC2 frame rotations for sources and copies; otherwise each volume's
	g4placement_type is honored, defaulting to GVolume's active convention. Missing meshes may
	be warned about beside a source file, but are never required during database generation.
	"""
	from .gvolume import GVolume

	file_dir = None
	if isinstance(source, (str, os.PathLike)):
		doc = load_cad_document(source)
		if warn_missing_meshes:
			file_dir = os.path.dirname(os.path.abspath(source))
	elif isinstance(source, dict):
		doc = source
	else:
		doc = {'volumes': source}
	if not isinstance(doc, dict):
		sys.exit(f"{GColors.RED}Error: CAD source did not parse into a mapping.{GColors.END}")

	volume_defaults = {**(doc.get('defaults') or {}), **(defaults or {})}
	mesh_dir = cad_dir if cad_dir is not None else doc.get('cad_dir', 'cad')
	extension = str(doc.get('extension', 'stl')).lstrip('.')
	volumes = []
	for entry in doc.get('volumes') or []:
		if not isinstance(entry, dict) or 'name' not in entry:
			sys.exit(f"{GColors.RED}Error: every CAD volume needs a 'name' (got {entry!r}).{GColors.END}")
		volume = _build_gvolume(GVolume, entry, volume_defaults, mesh_dir, extension, file_dir)
		if material_aliases:
			volume.material = material_aliases.get(volume.material, volume.material)
		if passive:
			volume.publish_passive(configuration)
		else:
			volume.publish(configuration)
		volumes.append(volume)
	return volumes


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
	volumes = doc.get('volumes') or []

	if not volumes:
		sys.exit(f"{GColors.RED}Error: CAD file {cad_file} lists no volumes.{GColors.END}")

	cfg = _upload_configuration(dbhost, experiment, system, variation, run, sqlite3,
	                            create_sqlite_database)

	print(f"  {GColors.BOLD}CAD upload{GColors.END} from {cad_file}")
	print(f"    experiment: {experiment}, system: {system}, variation: {variation}, run: {run}")

	for gvolume in build_cad(cfg, cad_file, warn_missing_meshes=True):
		if verbosity > 0:
			target = gvolume.parameters.split(',', 1)[0] if gvolume.solid == 'CAD' else gvolume.copyOf
			print(f"    + {gvolume.name:<24} -> {target}")

	cfg.sqlitedb.commit()
	print(f"  {GColors.GREEN}Uploaded {cfg.nvolumes} CAD volume(s){GColors.END} into {dbhost}")
	if getattr(cfg, 'use_pyvista', False):
		cfg.show()
	cfg.sqlitedb.close()


def _upload_configuration(dbhost, experiment, system, variation, run, sqlite3, create_sqlite_database):
	from .gconfiguration import GConfiguration, get_arguments

	# Parse an empty argv so we get the parser defaults without inheriting the
	# host process's sys.argv (e.g. pytest's -v collides with -v/--variation).
	args = get_arguments([])
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

	# A `copyOf` volume carries no mesh of its own: it reuses another CAD volume's solid, so it must
	# NOT be solid="CAD" (else the CAD factory would look for a mesh named after it). The g4 CAD
	# builder resolves the copy against the named source volume (same system).
	copy_of = merged.pop('copyOf', None)
	scale = merged.pop('scale', None)
	filename = merged.pop('file', f"{name}.{extension}")
	if copy_of is not None:
		gvolume.copyOf = str(copy_of)
	else:
		# Mark as a CAD import. The parameters column carries the runtime mesh path and uniform scale:
		# "<path>, <scale>". This keeps description available for normal descriptive text.
		gvolume.solid = 'CAD'
		# Runtime path, resolved by GEMC relative to the system directory (e.g. "stls/htccCone.stl").
		mesh_path = os.path.join(cad_dir, filename)
		if ',' in mesh_path:
			sys.exit(
				f"{GColors.RED}Error: CAD mesh paths cannot contain commas: '{mesh_path}'.{GColors.END}"
			)
		gvolume.parameters = f"{mesh_path}, {1 if scale is None else scale}"

		# Warn (do not fail) when the mesh is not found next to the definition file: the database may
		# be built on a different machine than the one that runs GEMC.
		local_mesh = os.path.join(file_dir, filename) if file_dir is not None else None
		if local_mesh is not None and not os.path.exists(local_mesh):
			print(f"  {GColors.YELLOW}Warning:{GColors.END} mesh not found next to definition file: {local_mesh}")

	rotation = merged.pop('rotation', None)
	if rotation is not None:
		gvolume.rotations = [str(rotation)]

	for key, value in merged.items():
		attr = _FIELD_MAP.get(key)
		if attr is None:
			sys.exit(f"{GColors.RED}Error: unknown CAD key '{key}' for volume '{name}'.{GColors.END}")
		setattr(gvolume, attr, value)

	if gvolume.material is None:
		gvolume.material = 'G4_AIR'

	return gvolume
