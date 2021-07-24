from pathlib import Path
from datetime import datetime

__all__ = ["backup_existing"]


def backup_existing(path: Path):
    """Creates a backup of existing files that would be overwritten."""
    if path.exists():
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        path.rename(
            path.with_name(
                f"{path.name.split('.')[0]}-{now}.bk{''.join(path.suffixes)}"
            )
        )
