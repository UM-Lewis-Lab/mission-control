import logging
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence
from datetime import datetime as datetime

from . import gdrive
from .gdrive import GDriveClient
from .logger import CSVLogger
from .util import backup_existing

__all__ = ["MissionControl"]


@dataclass
class MissionControl:
    project_name: str
    experiment_name: str
    run_name: str
    root_path: Path
    log_fields: Sequence[str]

    overwrite: bool = False
    project_metadata: Optional[dict] = None
    experiment_metadata: Optional[dict] = None
    run_metadata: Optional[dict] = None

    gdrive: GDriveClient = None
    backup_logs: bool = True
    backup_artifacts: bool = True

    project_path: Path = field(init=False)
    experiment_path: Path = field(init=False)
    run_path: Path = field(init=False)
    artifact_path: Path = field(init=False)
    log_path: Path = field(init=False)
    logger: CSVLogger = field(init=False)

    def __post_init__(self):
        # Ensure GDrive is connected if backups are enabled.
        if self.backup_logs or self.backup_artifacts:
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

        # Setup directory structure and record metadata
        self.project_path = self.root_path.expanduser().resolve / self.project_name
        self.experiment_path = self.project_path / self.experiment_name
        self.run_path = self.experiment_path / self.run_name
        self.log_path = self.run_path / "logs.csv"
        self.artifact_path = self.run_path / "artifacts"
        if not self.overwrite:
            backup_existing(self.log_path)
            backup_existing(self.artifact_path)
        for path, meta in [
            (self.project_path, self.project_metadata),
            (self.experiment_path, self.experiment_metadata),
            (self.run_path, self.run_metadata),
        ]:
            if not path.exists():
                path.mkdir(parents=True)
            if meta:
                write_path = path / "metadata.json"
                if not self.overwrite:
                    backup_existing(write_path)
                with write_path.open("w") as f:
                    json.dump(meta, f, indent=2)

        # Setup logger
        self.logger = CSVLogger(self.log_path, self.log_fields)

    def save_log(self, **kwargs):
        self.logger.write(**kwargs)
        # TODO: g-drive backup

    def save_artifact(self, obj: Any, name: str, metadata: dict = None):
        metadata = metadata or {}
        metadata["timestamp"] = datetime.now().isoformat()

        write_path = self.artifact_path / name
        meta_path = write_path.with_name(write_path.name.split(".")[0] + "-meta.json")

        with write_path.open("w") as f:
            pickle.dump(obj, f)

        with meta_path.open("w") as f:
            json.dump(metadata, f)

        # TODO: g-drive backup
