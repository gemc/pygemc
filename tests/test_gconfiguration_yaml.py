from pygemc.api.gconfiguration import GConfiguration, get_arguments


def test_read_yaml_pyvista_options_from_mapping(tmp_path):
    yaml_file = tmp_path / "detector.yaml"
    yaml_file.write_text(
        "\n".join(
            [
                "g4view:",
                '  background: "0.92 0.92 0.98"',
                "",
                "g4camera:",
                "  theta: 117*deg",
                "  phi: 166*deg",
            ]
        )
    )

    options = GConfiguration._read_yaml_pyvista_options(yaml_file)

    assert options == {
        "background_color": "0.92 0.92 0.98",
        "camera_theta": "117*deg",
        "camera_phi": "166*deg",
    }


def test_read_yaml_pyvista_options_from_saved_configuration_list(tmp_path):
    yaml_file = tmp_path / "gemc.saved_configuration.yaml"
    yaml_file.write_text(
        "\n".join(
            [
                "g4view:",
                "  - background: 1 1 1",
                "  - cloudPoints: 1000",
                "g4camera:",
                "  - phi: 0*deg",
                "  - theta: 0*deg",
            ]
        )
    )

    options = GConfiguration._read_yaml_pyvista_options(yaml_file)

    assert options == {
        "background_color": "1 1 1",
        "camera_phi": "0*deg",
        "camera_theta": "0*deg",
    }


def test_read_yaml_argument_is_loaded_by_configuration(tmp_path):
    yaml_file = tmp_path / "detector.yaml"
    db_file = tmp_path / "gemc.db"
    yaml_file.write_text(
        "\n".join(
            [
                "g4view:",
                "  background: 0.1 0.2 0.3",
                "g4camera:",
                "  theta: 90*deg",
                "  phi: 180*deg",
            ]
        )
    )
    args = get_arguments(
        [
            "--read-yaml",
            str(yaml_file),
            "-sql",
            str(db_file),
        ]
    )

    configuration = GConfiguration("examples", "detector", args=args, enable_pyvista=False)

    assert configuration.yaml_pyvista_options == {
        "background_color": "0.1 0.2 0.3",
        "camera_theta": "90*deg",
        "camera_phi": "180*deg",
    }


def test_yaml_camera_phi_gets_pyvista_z_rotation_offset():
    assert GConfiguration._pyvista_camera_angles(
        {
            "camera_theta": "90*deg",
            "camera_phi": "30*deg",
        }
    ) == (90.0, 210.0)


def test_default_pyvista_camera_angles_are_unchanged_without_yaml_phi():
    assert GConfiguration._pyvista_camera_angles({}) == (90.0, 0.0)
