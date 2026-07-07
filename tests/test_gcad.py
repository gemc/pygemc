import sqlite3

import pytest

from pygemc.api.gcad import upload_cad_definitions


CAD_YAML = """\
# HTCC cad pieces
system:    htcc
variation: default
run:       1
cad_dir:   cad

defaults:
  material: rohacell31
  color:    "888888"

volumes:
  - name:     htccMollerConeExt
    position: 0*cm, 0*cm, 0.1*cm
    rotation: 0*deg, 180*deg, 0*deg
  - name:     htccCone
    position: 0*cm, 0*cm, 0.0*cm
    material: G4_AIR
    sensitivity: flux
    identifier: "id: 3"
"""


def _write_cad_dir(tmp_path):
	"""Create a cad directory with a definition file and matching + extra STL files."""
	cad_dir = tmp_path / "cad"
	cad_dir.mkdir()
	# meshes: two are listed, one (htccMollerCone) is present but NOT listed
	for stem in ("htccMollerConeExt", "htccCone", "htccMollerCone"):
		(cad_dir / f"{stem}.stl").write_text("solid dummy\nendsolid dummy\n")
	cad_file = cad_dir / "cad__default.yaml"
	cad_file.write_text(CAD_YAML)
	return cad_file


def _rows(db):
	cur = db.execute(
		"SELECT name, solid, material, color, position, rotations, description, digitization, "
		"identifier FROM geometry ORDER BY name"
	)
	cols = [c[0] for c in cur.description]
	return [dict(zip(cols, row)) for row in cur.fetchall()]


def test_parser_matches_pyyaml_shape():
	# parse the YAML with the built-in block parser (independent of PyYAML availability)
	from pygemc.api.gcad import _parse_cad_yaml

	parsed = _parse_cad_yaml(CAD_YAML)
	assert parsed["system"] == "htcc"
	assert parsed["run"] == 1
	assert parsed["defaults"]["material"] == "rohacell31"
	assert parsed["defaults"]["color"] == "888888"
	assert len(parsed["volumes"]) == 2
	assert parsed["volumes"][0]["name"] == "htccMollerConeExt"
	assert parsed["volumes"][1]["identifier"] == "id: 3"


def test_only_listed_volumes_are_uploaded(tmp_path):
	cad_file = _write_cad_dir(tmp_path)
	db_path = tmp_path / "gemc.db"

	upload_cad_definitions(str(cad_file), str(db_path))

	db = sqlite3.connect(db_path)
	rows = _rows(db)
	names = {r["name"] for r in rows}

	# htccMollerCone.stl exists on disk but is not in the file -> must not be uploaded
	assert names == {"htccMollerConeExt", "htccCone"}
	assert all(r["solid"] == "CAD" for r in rows)


def test_uploaded_fields_and_aliases(tmp_path):
	cad_file = _write_cad_dir(tmp_path)
	db_path = tmp_path / "gemc.db"

	upload_cad_definitions(str(cad_file), str(db_path))

	db = sqlite3.connect(db_path)
	rows = {r["name"]: r for r in _rows(db)}

	ext = rows["htccMollerConeExt"]
	assert ext["material"] == "rohacell31"       # from defaults
	assert ext["color"] == "888888"
	assert ext["position"] == "0*cm, 0*cm, 0.1*cm"
	assert ext["rotations"] == "0*deg, 180*deg, 0*deg"
	assert ext["description"] == "cad/htccMollerConeExt.stl"

	cone = rows["htccCone"]
	assert cone["material"] == "G4_AIR"           # per-volume override wins over defaults
	assert cone["digitization"] == "flux"          # `sensitivity` alias -> digitization
	assert cone["identifier"] == "id: 3"           # `identifier` with a colon (quoted)


def test_json_input_is_accepted(tmp_path):
	cad_dir = tmp_path / "cad"
	cad_dir.mkdir()
	(cad_dir / "boxCad.stl").write_text("solid dummy\nendsolid dummy\n")
	cad_file = cad_dir / "cad.json"
	cad_file.write_text(
		'{"system": "test", "volumes": [{"name": "boxCad", "material": "G4_AIR"}]}'
	)
	db_path = tmp_path / "gemc.db"

	upload_cad_definitions(str(cad_file), str(db_path))

	db = sqlite3.connect(db_path)
	rows = _rows(db)
	assert len(rows) == 1
	assert rows[0]["name"] == "boxCad"
	assert rows[0]["solid"] == "CAD"
	assert rows[0]["description"] == "cad/boxCad.stl"


def test_missing_system_key_exits(tmp_path):
	cad_file = tmp_path / "bad.yaml"
	cad_file.write_text("volumes:\n  - name: x\n")
	with pytest.raises(SystemExit):
		upload_cad_definitions(str(cad_file), str(tmp_path / "gemc.db"))
