"""CAD publisher regressions, also runnable with the standard-library unittest runner."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

from pygemc import GVolume, build_cad
from pygemc.api.gcad import upload_cad_definitions
from pygemc.api.gsqlite import create_sqlite_database


class CADPublisherTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.directory = Path(self.work.name)
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        create_sqlite_database(self.db)
        self.cfg = SimpleNamespace(
            factory="sqlite", experiment="test", system="companion", variation="survey", runno=3029,
            sqlitedb=self.db, nvolumes=0, use_pyvista=False,
            geoFileName=str(self.directory / "geometry.txt"),
        )

    def test_gxml_passive_copies_and_optical_skins(self):
        source = self.directory / "placements.gxml"
        source.write_text('''<gxml>
  <volume name="cone" mother="gas" material="Air_Opt" color="E9C45D"
          position="1*cm 2*cm 3*cm" rotation="0 180*deg 0"
          sensitivity="mirror: coating" identifiers="optical-label" hitType="mirror" />
  <volume name="cone_copy" copyOf="cone" material="G4_Cu" color="abcdef"
          rotation="ordered: yzx 0*deg 30*deg 0*deg" />
</gxml>''')
        build_cad(self.cfg, source, cad_dir="stls", passive=True,
                  material_aliases={"Air_Opt": "G4_AIR_Optical"})
        rows = self.db.execute(
            "SELECT name, solid, parameters, mother, material, color, position, rotations, "
            "g4placement_type, copyOf, mirror, digitization, identifier FROM geometry ORDER BY name"
        ).fetchall()
        self.assertEqual(rows, [
            ("cone", "CAD", "stls/cone.stl, 1", "gas", "G4_AIR_Optical", "E9C45D",
             "1*cm, 2*cm, 3*cm", "0, 180*deg, 0", "passive", None, "coating", None, None),
            ("cone_copy", None, None, "root", "G4_Cu", "ABCDEF", "0*mm, 0*mm, 0*mm",
             "ordered: yzx, 0*deg, 30*deg, 0*deg", "passive", "cone", None, None, None),
        ])
        self.assertEqual(self.db.execute(
            "SELECT DISTINCT experiment, system, variation, run FROM geometry"
        ).fetchall(), [("test", "companion", "survey", 3029)])

    def check_existing_geometry_and_overrides(self, factory):
        self.cfg.factory = factory
        native = GVolume("existing")
        native.material = "G4_AIR"
        native.make_box(1, 1, 1)
        native.publish(self.cfg)
        document = {
            "experiment": "ignored", "system": "ignored", "variation": "ignored", "run": 1,
            "cad_dir": "original", "extension": ".ply",
            "defaults": {"material": "G4_Al", "color": "112233", "scale": 2},
            "volumes": [
                {"name": "mesh", "file": "shared.ply", "material": "G4_Cu", "scale": 3,
                 "rotation": "0*deg, 90*deg, 0*deg", "sensitivity": "flux", "identifiers": "id: 7"},
                {"name": "replica", "copyOf": "mesh", "g4placement_type": "passive"},
            ],
        }
        volumes = build_cad(self.cfg, document, cad_dir="runtime", defaults={"color": "abcdef"})
        self.assertEqual(self.cfg.nvolumes, 3)
        self.assertEqual(volumes[0].parameters, "runtime/shared.ply, 3")
        self.assertEqual(document["volumes"][0]["name"], "mesh")
        self.assertIsNone(volumes[1].solid)
        self.assertIsNone(volumes[1].parameters)
        if factory == "sqlite":
            self.assertEqual(self.db.execute("SELECT name FROM geometry ORDER BY name").fetchall(),
                             [("existing",), ("mesh",), ("replica",)])
            self.assertEqual(self.db.execute(
                "SELECT material, color, g4placement_type, digitization, identifier "
                "FROM geometry WHERE name='mesh'"
            ).fetchone(), ("G4_Cu", "ABCDEF", "active", "flux", "id: 7"))
        else:
            lines = (self.directory / "geometry.txt").read_text().splitlines()
            self.assertEqual(len(lines), 3)
            fields = [field.strip() for field in lines[1].split("|")]
            self.assertEqual(fields[:4], ["mesh", "CAD", "runtime/shared.ply, 3", "G4_Cu"])
            self.assertEqual(fields[7], "active")

    def test_ascii_keeps_existing_geometry(self):
        self.check_existing_geometry_and_overrides("ascii")

    def test_sqlite_keeps_existing_geometry(self):
        self.check_existing_geometry_and_overrides("sqlite")

    def test_calculated_placements_and_unknown_fields(self):
        placements = ({"name": f"cone{i}", "position": f"0*mm, 0*mm, {i}*mm"} for i in range(2))
        build_cad(self.cfg, placements, defaults={"material": "G4_Al"}, passive=True)
        self.assertEqual(self.cfg.nvolumes, 2)
        with self.assertRaisesRegex(SystemExit, "unknown CAD key"):
            build_cad(self.cfg, [{"name": "bad", "materail": "G4_Cu"}])

    def test_json_matches_cli_uploader_and_only_lists_selected_meshes(self):
        source = self.directory / "placements.json"
        source.write_text(json.dumps({
            "system": "ignored", "defaults": {"material": "G4_Al"},
            "volumes": [{"name": "source"}, {"name": "replica", "copyOf": "source"}],
        }))
        (self.directory / "unlisted.stl").write_text("solid extra\nendsolid extra\n")
        build_cad(self.cfg, source)
        output = self.directory / "upload.db"
        upload_cad_definitions(source, str(output), experiment="test", variation="survey", run=3029)
        with closing(sqlite3.connect(output)) as uploaded:
            expected = uploaded.execute("SELECT * FROM geometry ORDER BY name").fetchall()
        # The upload takes the system name from its document; build_cad keeps the supplied configuration.
        self.db.execute("UPDATE geometry SET system='ignored'")
        self.assertEqual(self.db.execute("SELECT * FROM geometry ORDER BY name").fetchall(), expected)
        self.assertEqual(self.cfg.nvolumes, 2)

    def test_yaml_document_and_explicit_zero_rotation(self):
        source = self.directory / "placements.yaml"
        source.write_text("""defaults:
  material: G4_Al
  g4placement_type: passive
cad_dir: stls
volumes:
  - name: bracket
    rotation: 0*deg, 0*deg, 0*deg
""")
        build_cad(self.cfg, source)
        self.assertEqual(self.db.execute(
            "SELECT parameters, rotations, g4placement_type FROM geometry"
        ).fetchone(), ("stls/bracket.stl, 1", "0*deg, 0*deg, 0*deg", "passive"))


if __name__ == "__main__":
    unittest.main()
