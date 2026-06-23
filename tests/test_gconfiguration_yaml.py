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


def test_show_formats_variations_and_run_as_table(tmp_path, capsys):
    args = get_arguments(["-sql", str(tmp_path / "gemc.db"), "-r", "3029"])
    configuration = GConfiguration(
        "examples",
        "detector",
        args=args,
        enable_pyvista=False,
    )
    configuration.init_variation("rga_spring2018")

    configuration.show()

    output = capsys.readouterr().out
    assert "Variation / Run:" in output
    assert "Variation" in output
    assert "Run" in output
    assert "default" in output
    assert "rga_spring2018" in output
    assert "3029" in output
    assert "(Variations, Run)" not in output


def test_show_uses_recorded_run_for_each_variation(tmp_path, capsys):
    args = get_arguments(["-sql", str(tmp_path / "gemc.db")])
    configuration = GConfiguration(
        "examples",
        "detector",
        args=args,
        enable_pyvista=False,
    )
    configuration.runno = 11
    configuration.record_current_variation_run()
    configuration.init_variation("ddvcs")
    configuration.runno = 10000001
    configuration.record_current_variation_run()

    configuration.show()

    output = capsys.readouterr().out
    assert "default                        11" in output
    assert "ddvcs                    10000001" in output


def test_show_prints_pyvista_variation(tmp_path, capsys):
    args = get_arguments(["-sql", str(tmp_path / "gemc.db")])
    configuration = GConfiguration(
        "examples",
        "detector",
        args=args,
        enable_pyvista=False,
    )
    configuration.use_pyvista = True
    configuration.pyvista_variation = "ddvcs"

    configuration.show()

    output = capsys.readouterr().out
    assert "PyVista Variation: ddvcs" in output
