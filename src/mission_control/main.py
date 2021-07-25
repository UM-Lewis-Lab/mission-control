import logging
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Optional, Sequence
from datetime import datetime

from . import gdrive
from .gdrive import GDriveClient, BackupService
from .logger import CSVLogger
from .util import backup_local_files

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
    backup_logs: bool = False
    backup_artifacts: bool = False
    log_backup_freq: int = 100
    gdrive_root: str = "mission-control"

    project_path: Path = None
    experiment_path: Path = None
    run_path: Path = None
    artifact_path: Path = None
    log_path: Path = None
    logger: CSVLogger = None

    backup_service: BackupService = None
    logs_since_backup: int = 0

    def __post_init__(self):
        # Ensure GDrive is connected if backups are enabled.
        backups_enabled = self.backup_logs or self.backup_artifacts
        if backups_enabled:
            if self.gdrive is None:
                try:
                    self.gdrive = gdrive.connect(root_folder_name=self.gdrive_root)
                except:
                    logging.info(
                        "If you do not wish to use gdrive, set gdrive=False or disable backups."
                    )
                    raise
            elif not self.gdrive:
                raise ValueError(
                    "Cannot disable gdrive without disabling logging. Please disable logging or enable gdrive."
                )
            self.backup_service = BackupService(
                self.gdrive,
                self.project_name,
                self.experiment_name,
                self.run_name,
                overwrite=self.overwrite,
                root_folder_name=self.gdrive_root,
            )

        # Setup directory structure and record metadata
        self.project_path = self.root_path.expanduser().resolve() / self.project_name
        self.experiment_path = self.project_path / self.experiment_name
        self.run_path = self.experiment_path / self.run_name
        self.log_path = self.run_path / "logs.csv"
        self.artifact_path = self.run_path / "artifacts"
        if not self.overwrite:
            backup_local_files(self.log_path)
            backup_local_files(self.artifact_path)
        for path, meta, level in [
            (self.project_path, self.project_metadata, "project"),
            (self.experiment_path, self.experiment_metadata, "experiment"),
            (self.run_path, self.run_metadata, "run"),
            (self.artifact_path, None, "artifact"),
        ]:
            if not path.exists():
                path.mkdir(parents=True)

            if meta:
                write_path = path / "metadata.json"
                if not self.overwrite:
                    backup_local_files(write_path)
                with write_path.open("w") as f:
                    json.dump(meta, f, indent=2)
                if backups_enabled:
                    # Backup metadata to GDrive
                    self.backup_service.backup(
                        dict(
                            local_path=write_path,
                            name=write_path.name,
                            mime_type="application/json",
                            folder_id=getattr(self.backup_service, f"{level}_folder"),
                            replace=self.overwrite,
                        )
                    )
        # Setup logger
        self.logger = CSVLogger(self.log_path, self.log_fields)

        # Call the tear-down process if python encounters an error.
        def hook(exctype, value, traceback):
            self.finish()
            sys.__excepthook__(exctype, value, traceback)

        sys.excepthook = hook

    def finish(self):
        if self.backup_service is not None:
            # Ensure that all logs are backed up to gdrive
            if self.backup_logs and self.logs_since_backup > 0:
                self.backup_service.backup(
                    dict(
                        local_path=self.log_path,
                        name=self.log_path.name,
                        folder_id=self.backup_service.run_folder,
                        replace=True,
                    )
                )
            self.backup_service.finish()

    def save_log(self, **kwargs):
        self.logger.write(**kwargs)
        self.logs_since_backup += 1
        if self.backup_logs and self.logs_since_backup >= self.log_backup_freq:
            self.backup_service.backup(
                dict(
                    local_path=self.log_path,
                    name=self.log_path.name,
                    folder_id=self.backup_service.run_folder,
                    replace=True,
                )
            )
            self.logs_since_backup = 0

    def save_artifact(self, obj: Any, name: str, metadata: dict = None):
        metadata = metadata or {}
        metadata["timestamp"] = datetime.now().isoformat()

        write_path = self.artifact_path / f"{name}.pkl"
        meta_path = write_path.with_name(write_path.name.split(".")[0] + "-meta.json")

        with write_path.open("wb") as f:
            pickle.dump(obj, f)

        with meta_path.open("w") as f:
            json.dump(metadata, f)

        if self.backup_artifacts:
            for p in [write_path, meta_path]:
                self.backup_service.backup(
                    dict(
                        local_path=p,
                        name=p.name,
                        folder_id=self.backup_service.artifact_folder,
                        replace=True,
                    )
                )
