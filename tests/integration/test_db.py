from collections.abc import Iterator

import psycopg
import pytest

from dossier.common.db import connect

pytestmark = pytest.mark.integration


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    try:
        c = connect(timeout=3)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres not reachable: {exc}")
    with c:
        yield c


def test_can_connect(conn: psycopg.Connection) -> None:
    assert conn.execute("select 1").fetchone() == (1,)


def test_pgvector_distance(conn: psycopg.Connection) -> None:
    conn.execute("create extension if not exists vector")
    row = conn.execute("select '[1,2,3]'::vector <-> '[1,2,4]'::vector").fetchone()
    assert row is not None
    assert row[0] == pytest.approx(1.0)