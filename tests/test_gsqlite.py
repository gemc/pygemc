import sqlite3
from types import SimpleNamespace

import pytest

from pygemc.api.gsqlite import (
    _build_where_clause,
    create_sqlite_database,
    show_volumes_from_database,
)
from pygemc.api.gvolume import _OPTIONAL_GEOMETRY_FIELDS, GVolume


def _args(**overrides):
    defaults = {
        "ef": None,
        "vf": None,
        "sf": None,
        "rf": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _geometry_database():
    db = sqlite3.connect(":memory:")
    db.execute(
        """CREATE TABLE geometry (
            id integer primary key,
            experiment text,
            variation text,
            system text,
            run integer,
            name text
        )"""
    )
    db.executemany(
        """INSERT INTO geometry (experiment, variation, system, run, name)
           VALUES (?, ?, ?, ?, ?)""",
        [
            ("expA", "default", "dc", 1, "row_one"),
            ("expB", "default", "dc", 1, "row_two"),
            ("quote'exp", "default", "dc", 1, "quoted_row"),
        ],
    )
    return db


def test_gsqlite_filter_returns_matching_row(capsys):
    where_clause, params = _build_where_clause(_args(ef="expA"))

    show_volumes_from_database(_geometry_database(), "name", where_clause, params)

    output = capsys.readouterr().out
    assert "row_one" in output
    assert "row_two" not in output
    assert "quoted_row" not in output


def test_gsqlite_filter_treats_quote_as_literal(capsys):
    where_clause, params = _build_where_clause(_args(ef="quote'exp"))

    show_volumes_from_database(_geometry_database(), "name", where_clause, params)

    output = capsys.readouterr().out
    assert "quoted_row" in output
    assert "row_one" not in output
    assert "row_two" not in output


def test_gsqlite_filter_treats_injection_as_literal(capsys):
    where_clause, params = _build_where_clause(_args(ef="' OR '1'='1"))

    show_volumes_from_database(_geometry_database(), "name", where_clause, params)

    output = capsys.readouterr().out
    assert "row_one" not in output
    assert "row_two" not in output
    assert "quoted_row" not in output


def test_gsqlite_unknown_what_column_is_rejected():
    where_clause, params = _build_where_clause(_args())

    with pytest.raises(SystemExit):
        show_volumes_from_database(_geometry_database(), "name, missing_column", where_clause, params)


def test_sqlite_geometry_serializes_optional_fields_as_sql_null():
    database = sqlite3.connect(":memory:")
    create_sqlite_database(database)
    configuration = SimpleNamespace(
        factory="sqlite",
        sqlitedb=database,
        experiment="optional-boundary-test",
        system="test",
        variation="default",
        runno=1,
        nvolumes=0,
        use_pyvista=False,
    )
    volume = GVolume("optional_box")
    volume.make_box(1, 2, 3)
    volume.material = "G4_AIR"

    for field, unset_alias in zip(
        _OPTIONAL_GEOMETRY_FIELDS,
        (" none ", "", "~", "no", " null ", "not provided"),
    ):
        setattr(volume, field, unset_alias)

    volume.publish(configuration)

    columns = ", ".join(_OPTIONAL_GEOMETRY_FIELDS)
    stored_values = database.execute(
        f"SELECT {columns} FROM geometry WHERE name = ?", (volume.name,)
    ).fetchone()
    assert stored_values == (None,) * len(_OPTIONAL_GEOMETRY_FIELDS)
    geometry_columns = {
        row[1] for row in database.execute("PRAGMA table_info(geometry)").fetchall()
    }
    assert "_value_formatter" not in geometry_columns
    database.close()
