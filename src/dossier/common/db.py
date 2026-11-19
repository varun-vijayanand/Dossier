import psycopg

from dossier.common.config import get_settings


def connect(timeout: int = 5) -> psycopg.Connection:
    """Open a new Postgres connection using the configured URL."""
    return psycopg.connect(get_settings().database_url, connect_timeout=timeout)