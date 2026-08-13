import numpy as np

from pygemc.api.gconfiguration import GConfiguration, get_arguments
from pygemc.api.gvolume import GVolume
from pygemc.api import pyvista_api


class FakeMesh:
    def __init__(self, merged_count=1, points=None):
        self.points = np.zeros((8, 3)) if points is None else np.array(points, dtype=float)
        self.merged_count = merged_count

    def copy(self):
        copied = FakeMesh(merged_count=self.merged_count)
        copied.points = self.points.copy()
        return copied

    def extract_feature_edges(self, **kwargs):
        return self


class FakeMultiBlock:
    def __init__(self, meshes):
        self.meshes = meshes

    def combine(self, merge_points=False):
        return FakeMesh(merged_count=len(self.meshes))


class FakePv:
    def __init__(self):
        self.read_paths = []

    def Cube(self, **kwargs):
        return FakeMesh()

    def read(self, path):
        self.read_paths.append(path)
        return FakeMesh(points=[[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])

    def MultiBlock(self, meshes):
        return FakeMultiBlock(meshes)


class FakeActorProp:
    pass


class FakeActor:
    def __init__(self):
        self.prop = FakeActorProp()


class FakeConfiguration:
    def __init__(
        self,
        verbosity,
        variation="default",
        pyvista_variation=None,
        pyvista_fast=None,
        pyvista_fast_threshold=1000,
    ):
        self.use_pyvista = True
        self.pv = FakePv()
        self.verbosity = verbosity
        self.variation = variation
        self.pyvista_variation = pyvista_variation
        self.pyvista_fast = pyvista_fast
        self.pyvista_fast_threshold = pyvista_fast_threshold
        self.dbhost = None
        self._pyvista_render_entries = []
        self._pyvista_render_entries_flushed = False
        self.add_mesh_calls = 0
        self.added_meshes = []
        self.add_mesh_kwargs = []

    def add_mesh(self, *args, **kwargs):
        self.add_mesh_calls += 1
        self.added_meshes.append(args[0])
        self.add_mesh_kwargs.append(kwargs)
        return FakeActor()


def _box_volume():
    volume = GVolume("box")
    volume.make_box(1, 2, 3)
    volume.material = "G4_AIR"
    return volume


def _cad_volume(mesh_path):
    volume = GVolume("organ")
    volume.solid = "CAD"
    volume.parameters = f"{mesh_path}, 2"
    volume.material = "G4_WATER"
    volume.position = "1*mm, 2*mm, 3*mm"
    volume.description = "Organ mesh"
    volume.color = "ff0000"
    volume.gcolor = "ff0000"
    volume.opacity = 0.4
    return volume


def test_pyvista_volume_log_is_quiet_by_default(capsys):
    pyvista_api.render_volume(_box_volume(), FakeConfiguration(verbosity=0))

    assert "Volume:" not in capsys.readouterr().out


def test_pyvista_volume_log_is_printed_with_verbosity(capsys):
    pyvista_api.render_volume(_box_volume(), FakeConfiguration(verbosity=1))

    assert "Volume: box" in capsys.readouterr().out


def test_cli_verbosity_overrides_constructor_default(tmp_path):
    args = get_arguments(["--verbosity", "2", "-sql", str(tmp_path / "gemc.db")])

    configuration = GConfiguration("examples", "detector", args=args, verbosity=0, enable_pyvista=False)

    assert configuration.verbosity == 2


def test_pyvista_renders_only_requested_variation():
    configuration = FakeConfiguration(
        verbosity=0,
        variation="default",
        pyvista_variation="shifted",
    )

    pyvista_api.render_volume(_box_volume(), configuration)
    configuration.variation = "shifted"
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 1


def test_pyvista_defaults_to_first_rendered_variation():
    configuration = FakeConfiguration(verbosity=0, variation="default")

    pyvista_api.render_volume(_box_volume(), configuration)
    configuration.variation = "shifted"
    pyvista_api.render_volume(_box_volume(), configuration)
    configuration.variation = "default"
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 2


def test_cli_pyvista_variation_is_stored(tmp_path):
    args = get_arguments(["--pyvista-variation", "shifted", "-sql", str(tmp_path / "gemc.db")])

    configuration = GConfiguration("examples", "detector", args=args, enable_pyvista=False)

    assert configuration.pyvista_variation == "shifted"


def test_pyvista_fast_batches_matching_entries():
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=True)

    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 1
    assert configuration.added_meshes[0].merged_count == 2


def test_pyvista_detailed_mode_keeps_one_actor_per_volume():
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)

    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 2


def test_pyvista_auto_fast_uses_threshold():
    configuration = FakeConfiguration(
        verbosity=0,
        pyvista_fast=None,
        pyvista_fast_threshold=1,
    )

    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 1


def test_pyvista_flush_can_accept_later_volumes():
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)

    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)
    pyvista_api.render_volume(_box_volume(), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 2


def test_cli_pyvista_fast_options_are_stored(tmp_path):
    args = get_arguments(
        [
            "--pyvista-fast",
            "--pyvista-fast-threshold",
            "2500",
            "-sql",
            str(tmp_path / "gemc.db"),
        ]
    )

    configuration = GConfiguration("examples", "detector", args=args, enable_pyvista=False)

    assert configuration.pyvista_fast is True
    assert configuration.pyvista_fast_threshold == 2500


def test_cli_no_pyvista_fast_is_stored(tmp_path):
    args = get_arguments(["--no-pyvista-fast", "-sql", str(tmp_path / "gemc.db")])

    configuration = GConfiguration("examples", "detector", args=args, enable_pyvista=False)

    assert configuration.pyvista_fast is False


def test_pyvista_loads_cad_mesh_relative_to_sqlite_database(tmp_path):
    mesh_dir = tmp_path / "stls"
    mesh_dir.mkdir()
    mesh = mesh_dir / "organ.stl"
    mesh.write_text("solid organ\nendsolid organ\n")
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)
    configuration.dbhost = str(tmp_path / "gemc.db")

    pyvista_api.render_volume(_cad_volume("stls/organ.stl"), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.pv.read_paths == [str(mesh)]
    assert configuration.add_mesh_calls == 1
    assert np.allclose(
        configuration.added_meshes[0].points,
        np.array([[3.0, 2.0, 3.0], [1.0, 6.0, 3.0], [1.0, 2.0, 9.0]]),
    )


def test_pyvista_loads_cad_mesh_from_system_subdirectory(tmp_path):
    mesh_dir = tmp_path / "ltcc" / "stls"
    mesh_dir.mkdir(parents=True)
    mesh = mesh_dir / "organ.stl"
    mesh.write_text("solid organ\nendsolid organ\n")
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)
    configuration.dbhost = str(tmp_path / "gemc.db")
    configuration.system = "ltcc"

    pyvista_api.render_volume(_cad_volume("stls/organ.stl"), configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.pv.read_paths == [str(mesh)]
    assert configuration.add_mesh_calls == 1


def test_pyvista_cad_mesh_uses_modified_display_attributes(tmp_path):
    mesh = tmp_path / "organ.stl"
    mesh.write_text("solid organ\nendsolid organ\n")
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)
    volume = _cad_volume(str(mesh))
    volume.visible = 0
    volume.style = 0

    pyvista_api.render_volume(volume, configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.add_mesh_calls == 1
    assert configuration.add_mesh_kwargs[0]["color"] == "ff0000"
    assert configuration.add_mesh_kwargs[0]["opacity"] == 0.05


def test_pyvista_accepts_legacy_cad_parameter_layout(tmp_path):
    mesh = tmp_path / "organ.stl"
    mesh.write_text("solid organ\nendsolid organ\n")
    configuration = FakeConfiguration(verbosity=0, pyvista_fast=False)
    volume = _cad_volume(str(mesh))
    volume.parameters = "2"
    volume.description = str(mesh)

    pyvista_api.render_volume(volume, configuration)
    pyvista_api.flush_pyvista_rendering(configuration)

    assert configuration.pv.read_paths == [str(mesh)]
    assert configuration.add_mesh_calls == 1
