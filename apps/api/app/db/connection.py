from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

