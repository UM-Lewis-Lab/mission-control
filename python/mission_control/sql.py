import os

from playhouse.postgres_ext import PostgresqlExtDatabase

from .model import *

__all__ = ["connect"]

PG_DATABASE = os.getenv("PGDATABASE", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", 5432)
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASS", None)


def connect(
    database: str = None,
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
) -> PostgresqlExtDatabase:
    postgres_db.init(
        database or PG_DATABASE,
        host=host or PG_HOST,
        port=port or PG_PORT,
        user=user or PG_USER,
        password=password or PG_PASS,
    )
    postgres_db.create_tables(ALL_TABLES, safe=True)
    return postgres_db


class SQLLogger:
    def __init__(
        self,
        client: PostgresqlExtDatabase,
        project_name: str,
        project_metdata: dict,
        experiment_name: str,
        experiment_metadata: dict,
        run_name: str,
        run_metadata: dict,
    ):
        self.client = client
        self.project: Project = Project.get_or_create(
            name=project_name, metadata=project_metdata
        )
        self.experiment: Experiment = self.project.get_experiment(
            name=experiment_name, metadata=experiment_metadata
        )
        self.run: Run = self.experiment.get_run(name=run_name, metadata=run_metadata)

