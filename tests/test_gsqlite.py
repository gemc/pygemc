import sqlite3
from types import SimpleNamespace

import pytest

from pygemc.api.gsqlite import _build_where_clause, show_volumes_from_database


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
