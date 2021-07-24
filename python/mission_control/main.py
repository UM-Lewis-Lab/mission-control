from typing import Literal, Optional
from dataclasses import dataclass, field
import logging

from playhouse.postgres_ext import PostgresqlExtDatabase

from . import gdrive, sql
from .gdrive import GDriveClient


@dataclass
class MissionControl:
    project_name: str
    experiment_name: str
    log_backend: Literal["csv", "sql"] = "csv"
    sql_kwargs: Optional[dict] = None
    backup_logs: bool = True
    backup_artifacts: bool = True

    gdrive: GDriveClient = None
    sql: PostgresqlExtDatabase = None

    def __post_init__(self):
        backups_enabled = self.backup_logs or self.backup_artifacts
        if backups_enabled:
            if self.gdrive is None:
                try:
                    self.gdrive = gdrive.connect()
                except:
                    logging.info(
                        "If you do not wish to use gdrive, set gdrive=False or disable backups."
                    )
            elif not self.gdrive:
                raise ValueError(
                    "Cannot disable gdrive without disabling logging. Please disable logging or enable gdrive."
                )
        if self.sql is None and self.log_backend == "sql":
            self.sql = sql.connect()
    

