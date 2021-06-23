import os

from .model import *

PG_DATABASE = os.getenv("PGDATABASE", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", 5432)
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASS", None)


class MissionControl:
    def __init__(
        self,
        database: str = None,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
    ):
        self.db = postgres_db
        self.db.init(
            database or PG_DATABASE,
            host=host or PG_HOST,
            port=port or PG_PORT,
            user=user or PG_USER,
            password=password or PG_PASS,
        )
        self.db.create_tables(ALL_TABLES, safe=True)

    