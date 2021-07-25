from pathlib import Path
from datetime import datetime

__all__ = ["backup_timestamp", "backup_local_files"]


def backup_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def backup_local_files(path: Path):
    """Creates a backup of existing local files that would be overwritten."""
    if path.exists():
        path.rename(
            path.with_name(
                f"{path.name.split('.')[0]}-{backup_timestamp()}.bk{''.join(path.suffixes)}"
            )
        )
