import numpy as np

from pygemc.api.gconfiguration import GConfiguration, get_arguments
from pygemc.api.gvolume import GVolume
from pygemc.api import pyvista_api


class FakeMesh:
    def __init__(self, merged_count=1):
        self.points = np.zeros((8, 3))
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
    def Cube(self, **kwargs):
        return FakeMesh()

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
        self._pyvista_render_entries = []
        self._pyvista_render_entries_flushed = False
        self.add_mesh_calls = 0
        self.added_meshes = []

    def add_mesh(self, *args, **kwargs):
        self.add_mesh_calls += 1
        self.added_meshes.append(args[0])
        return FakeActor()


def _box_volume():
    volume = GVolume("box")
    volume.make_box(1, 2, 3)
    volume.material = "G4_AIR"
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
