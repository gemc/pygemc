"""Regression coverage for RICH aerogel scattering and roughness surfaces."""

from types import SimpleNamespace
import sqlite3

import pytest
from pygemc import GMaterial, GMirror
from pygemc.api.gsqlite import create_sqlite_database


@pytest.mark.parametrize("factory", ["ascii", "sqlite"])
def test_mie_properties_survive_publication(tmp_path, factory):
    database = sqlite3.connect(tmp_path / "optics.sqlite")
    create_sqlite_database(database)
    output = tmp_path / "materials.txt"
    configuration = SimpleNamespace(factory=factory, matFileName=str(output), sqlitedb=database,
                                    experiment="test", system="optics", variation="default", runno=11,
                                    nmaterials=0)
    material = GMaterial("aerogel")
    material.density = 0.23
    material.addMaterialWithFractionalMass("G4_SILICON_DIOXIDE", 1.0)
    material.photonEnergy = "2*eV 3*eV"
    material.indexOfRefraction = "1.05 1.05"
    material.mie = "15.12*cm 15.12*cm"
    material.mieforward, material.miebackward, material.mieratio = 0.999, 1, 1
    material.publish(configuration)
    if factory == "sqlite":
        actual = database.execute("SELECT mie, mieforward, miebackward, mieratio FROM materials").fetchone()
        assert actual == (material.mie, 0.999, 1, 1)
    else:
        fields = [field.strip() for field in output.read_text().split("|")][:-1]
        assert len(fields) == 22
        assert fields[-4:] == [material.mie, "0.999", "1", "1"]
    database.close()


@pytest.mark.parametrize("kind, valid", [("dielectric_dielectric", True), ("dielectric_metal", False)])
def test_roughness_only_surface_requires_dielectric_boundary(kind, valid):
    surface = GMirror("aerogel_roughness")
    surface.type, surface.finish, surface.model, surface.border = kind, "ground", "unified", "SkinSurface"
    surface.photonEnergy, surface.sigmaAlpha = "2*eV 3*eV", 0.006
    if valid:
        surface.check_validity()
    else:
        with pytest.raises(SystemExit):
            surface.check_validity()
